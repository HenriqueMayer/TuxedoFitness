"""Strict routine envelopes and single-consumption, non-retried batch writes."""

import difflib
import json
import re
from datetime import timedelta

from django.db import DatabaseError, transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from integrations.dtos import payload_hash
from integrations.hevy import HevyError
from integrations.models import IntegrationState
from integrations.routines import RoutinePayloadValidator, RoutineValidationError
from integrations.services import IncrementalSyncService, PlanRefreshService
from planning.models import RoutineProposal
from planning.prompts import PLACEHOLDER, json_text
from training.models import Routine


class SecretInputError(RoutineValidationError):
    pass


def parse_document(text):
    # Never echo a pasted credential, including when the document is malformed.
    for match in re.finditer(
        r'["\'](?:api_key|api-key)["\']\s*:\s*["\']([^"\']*)', text, re.I
    ):
        if match.group(1) != PLACEHOLDER:
            raise SecretInputError(
                _(
                    "Use only the literal API key placeholder. The pasted document was cleared."
                )
            )
    if len(text.encode()) > 2_000_000:
        raise RoutineValidationError(_("The document exceeds 2 MB."))
    if "```" in text:
        blocks = re.findall(r"```json\s*\n?(.*?)```", text, re.S | re.I)
        if len(blocks) != 1 or text.count("```") != 2:
            raise RoutineValidationError(_("Provide exactly one fenced json block."))
        text = blocks[0]

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    try:
        result = json.loads(
            text,
            object_pairs_hook=pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
        )
        pending = [result]
        while pending:
            value = pending.pop()
            if isinstance(value, dict):
                for key, item in value.items():
                    if key.lower() in {"api_key", "api-key"} and item != PLACEHOLDER:
                        raise SecretInputError(
                            _(
                                "Use only the literal API key placeholder. The pasted document was cleared."
                            )
                        )
                    pending.append(item)
            elif isinstance(value, list):
                pending.extend(value)
        return result
    except SecretInputError:
        raise

    except (ValueError, RecursionError):
        raise RoutineValidationError(
            _("Invalid JSON: check syntax, duplicate keys and numeric values.")
        ) from None


def validate_envelope(account, payload):
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version",
        "api_key",
        "operations",
    }:
        raise RoutineValidationError(
            _("The envelope requires only schema_version, api_key and operations.")
        )
    if type(payload["schema_version"]) is not int or payload["schema_version"] != 1:
        raise RoutineValidationError(_("Unsupported schema_version. Use 1."))
    if payload["api_key"] != PLACEHOLDER:
        raise SecretInputError(_("Use only the literal API key placeholder."))
    operations = payload["operations"]
    if not isinstance(operations, list) or not 1 <= len(operations) <= 20:
        raise RoutineValidationError(
            _("operations must contain between 1 and 20 items.")
        )
    validator = RoutinePayloadValidator(account)
    routine_ids = set(
        Routine.objects.filter(hevy_account=account).values_list(
            "external_id", flat=True
        )
    )
    seen = set()
    cleaned = []
    for index, operation in enumerate(operations):
        label = f"operations[{index}]"
        if not isinstance(operation, dict):
            raise RoutineValidationError(f"{label}: " + _("Expected an object."))
        action = operation.get("action")
        if not isinstance(action, str) or action not in {"create", "update"}:
            raise RoutineValidationError(
                f"{label}.action: " + _("Choose create or update.")
            )
        allowed = {"action", "routine"} | (
            {"routine_id"} if action == "update" else set()
        )
        if set(operation) != allowed:
            raise RoutineValidationError(
                f"{label}: " + _("Unexpected or missing operation fields.")
            )
        identifier = operation.get("routine_id")
        if action == "update":
            if (
                not isinstance(identifier, str)
                or identifier not in routine_ids
                or identifier in seen
            ):
                raise RoutineValidationError(
                    f"{label}.routine_id: "
                    + _("Unknown, foreign or repeated routine ID.")
                )
            seen.add(identifier)
        try:
            routine = validator.validate({"routine": operation["routine"]})["routine"]
        except RoutineValidationError as error:
            raise RoutineValidationError(f"{label}.{error}") from None
        groups = {}
        for exercise in routine["exercises"]:
            group = exercise["superset_id"]
            if group is not None:
                groups[group] = groups.get(group, 0) + 1
        if any(count < 2 for count in groups.values()):
            raise RoutineValidationError(
                f"{label}.routine.exercises: "
                + _("A superset needs at least two exercises.")
            )
        if len(json_text({"routine": routine}).encode()) > 65_536:
            raise RoutineValidationError(f"{label}: " + _("A routine exceeds 64 KB."))
        cleaned.append({**operation, "routine": routine})
    return {"schema_version": 1, "api_key": PLACEHOLDER, "operations": cleaned}


def preview(account, payload, client):
    payload = validate_envelope(account, payload)
    versions, changes = {}, []
    for operation in payload["operations"]:
        before = {}
        if operation["action"] == "update":
            before = client.get_routine_payload(operation["routine_id"])
            versions[operation["routine_id"]] = payload_hash(before)
        after = operation["routine"]
        # Include all original fields in the before pane; response-only fields are labeled.
        changes.append(
            {
                "action": operation["action"],
                "title": after["title"],
                "before": json_text(before),
                "after": json_text(after),
                "diff": "\n".join(
                    difflib.unified_diff(
                        json_text(before).splitlines(),
                        json_text(after).splitlines(),
                        fromfile="Hevy (response)",
                        tofile="Proposed prescription",
                        lineterm="",
                    )
                ),
            }
        )
    return RoutineProposal.objects.create(
        account=account,
        payload=payload,
        source_versions=versions,
        changes=changes,
        expires_at=timezone.now() + timedelta(minutes=15),
        results=[{"state": "not_executed"} for _ in payload["operations"]],
    )


def submit(account, proposal_id, client):
    IncrementalSyncService._acquire_lock(account)
    try:
        with transaction.atomic():
            proposal = RoutineProposal.objects.select_for_update().get(
                pk=proposal_id, account=account
            )
            if proposal.state != "previewed":
                raise RoutineValidationError(
                    _("This confirmation has already been consumed.")
                )
            if proposal.expires_at <= timezone.now():
                proposal.state = "expired"
            else:
                proposal.state = "submitting"
                proposal.submitted_at = timezone.now()
            proposal.save(update_fields=["state", "submitted_at"])
        if proposal.state == "expired":
            return proposal
        try:
            validate_envelope(account, proposal.payload)
            for identifier, original_hash in proposal.source_versions.items():
                if (
                    payload_hash(client.get_routine_payload(identifier))
                    != original_hash
                ):
                    proposal.state = "conflict"
                    proposal.save(update_fields=["state"])
                    return proposal
        except (HevyError, ValueError):
            proposal.state = "failed"
            proposal.save(update_fields=["state"])
            return proposal
        results = proposal.results
        for index, operation in enumerate(proposal.payload["operations"]):
            results[index] = {"state": "submitting"}
            proposal.results = results
            proposal.save(update_fields=["results"])
            try:
                IncrementalSyncService._assert_lock(account)
                if operation["action"] == "create":
                    dto = client.create_routine({"routine": operation["routine"]})
                else:
                    dto = client.update_routine(
                        operation["routine_id"], {"routine": operation["routine"]}
                    )
                results[index] = {"state": "succeeded", "routine_id": dto.external_id}
            except (HevyError, OSError) as error:
                code = error.code if isinstance(error, HevyError) else "WRITE_UNKNOWN"
                results[index] = {
                    "state": "unknown" if code == "WRITE_UNKNOWN" else "failed",
                    "code": code,
                }
                proposal.state = (
                    "unknown"
                    if code == "WRITE_UNKNOWN"
                    else "partial"
                    if index
                    else "failed"
                )
                break
            finally:
                proposal.results = results
                proposal.save(update_fields=["results"])
        else:
            proposal.state = "succeeded"
        proposal.local_refresh_pending = any(
            item["state"] == "succeeded" for item in results
        )
        proposal.save(update_fields=["state", "local_refresh_pending"])
    finally:
        IncrementalSyncService._release_lock(account)
    if proposal.local_refresh_pending:
        try:
            PlanRefreshService(client).run(account.user)
            proposal.local_refresh_pending = False
            proposal.save(update_fields=["local_refresh_pending"])
        except (HevyError, DatabaseError, ValueError):
            IntegrationState.objects.filter(hevy_account=account).update(is_stale=True)
    return proposal
