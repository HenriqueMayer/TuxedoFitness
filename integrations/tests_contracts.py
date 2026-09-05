"""Provider-boundary cases against synthetic bytes, never real endpoints."""

import copy
import csv
import json
from datetime import timedelta
from io import BytesIO, StringIO
from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError, URLError

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from integrations import dtos
from integrations.hevy import (
    HevyClient,
    HevyError,
    NoRedirect,
    default_transport,
    default_write_transport,
    urlopen,
)
from integrations.models import ProviderSnapshot, SyncLock
from integrations.routines import RoutinePayloadValidator, RoutineValidationError
from integrations.services import IncrementalSyncService
from integrations.tests_sync import response, routine, template, workout
from planning.models import RoutineProposal
from planning.prompts import example_payload
from training.tests.factories import (
    create_account,
    create_routine,
    create_template,
    create_workout,
)


class BoundaryTests(TestCase):
    def test_aliases_preserve_raw_values_and_reject_conflicts(self):
        source = template()
        source["equipment"] = source.pop("equipment_category")
        dto = dtos.ExerciseTemplateDTO.from_payload(source)
        self.assertEqual(dto.equipment_category, "barbell")
        self.assertEqual(dto.raw_payload, source)
        source["equipment_category"] = "machine"
        with self.assertRaises(dtos.PayloadError):
            dtos.ExerciseTemplateDTO.from_payload(source)
        source = routine()
        source["notes"] = "Preserved notes"
        exercise = source["exercises"][0]
        exercise["superset_id"] = exercise.pop("supersets_id")
        dto = dtos.RoutineDTO.from_payload(source)
        self.assertEqual(dto.raw_payload["notes"], "Preserved notes")
        exercise["supersets_id"] = 2
        with self.assertRaises(dtos.PayloadError):
            dtos.RoutineDTO.from_payload(source)

    def test_scalar_contracts_reject_malformed_values(self):
        cases = [
            (dtos.nullable_string, 1),
            (dtos.nullable_datetime, 1),
            (dtos.nullable_datetime, "bad"),
            (dtos.nullable_datetime, "2026-01-01T12:00:00"),
            (dtos.nullable_decimal, True),
            (dtos.nullable_decimal, {}),
            (dtos.nullable_decimal, "bad"),
            (dtos.nullable_decimal, "NaN"),
            (dtos.nullable_decimal, -1),
            (dtos.nullable_integer, True),
            (dtos.nullable_integer, "bad"),
            (dtos.nullable_integer, {}),
            (dtos.nullable_integer, -1),
            (dtos.nullable_integer, 1.5),
            (dtos.required_integer, None),
            (dtos.required_list, [1]),
        ]
        for parser, value in cases:
            with (
                self.subTest(parser=parser, value=value),
                self.assertRaises(dtos.PayloadError),
            ):
                parser({"field": value}, "field")
        for value in [[], False]:
            with self.assertRaises(dtos.PayloadError):
                dtos.AccountDTO.from_payload({"data": value})
        for key, value in [("secondary_muscle_groups", [1]), ("is_custom", 1)]:
            with self.assertRaises(dtos.PayloadError):
                dtos.ExerciseTemplateDTO.from_payload({**template(), key: value})

    def test_set_workout_and_event_contracts(self):
        source = workout()["exercises"][0]["sets"][0]
        for changes in [
            {"rep_range": []},
            {"rep_range": {"start": 9, "end": 8}},
            {"rpe": 5},
            {"type": "invented"},
        ]:
            with self.assertRaises(dtos.PayloadError):
                dtos.set_dto({**source, **changes}, routine=False)
        for changes in [{"start_time": None}, {"end_time": "2025-01-01T00:00:00Z"}]:
            with self.assertRaises(dtos.PayloadError):
                dtos.WorkoutDTO.from_payload({**workout(), **changes})
        for payload in [
            {"type": "deleted", "id": "x"},
            {"type": "other"},
            {"type": "updated", "workout": None},
            {"type": "updated", "workout": {"id": "x"}},
        ]:
            with self.assertRaises(dtos.PayloadError):
                dtos.WorkoutEventDTO.from_payload(payload)

    def test_update_method_response_identity_and_safe_dynamic_paths(self):
        calls = []

        def transport(url, headers, body, timeout, method):
            calls.append((url, headers, json.loads(body), method))
            return response(routine("owned"))

        client = HevyClient("synthetic-key", write_transport=transport)
        dto = client.update_routine("owned", {"routine": {"title": "A"}})
        self.assertEqual(dto.external_id, "owned")
        self.assertEqual(calls[0][3], "PUT")
        self.assertEqual(calls[0][0], "https://api.hevyapp.com/v1/routines/owned")
        self.assertEqual(set(calls[0][2]), {"routine"})
        for identifier in ["", "..", "a/b", "a?b", "https://evil.test"]:
            with self.subTest(identifier=identifier), self.assertRaises(HevyError):
                client.update_routine(identifier, {})
        client = HevyClient(
            "synthetic-key",
            write_transport=lambda *a, **k: response(routine("different")),
        )
        with self.assertRaises(HevyError) as error:
            client.update_routine("owned", {})
        self.assertEqual(error.exception.code, "WRITE_UNKNOWN")
        for payload in [routine("owned"), {"routine": routine("owned")}]:
            client = HevyClient("synthetic-key", transport=lambda *_: response(payload))
            self.assertEqual(client.get_routine_payload("owned")["id"], "owned")
        for payload in [{}, routine("different"), {"routine": None}]:
            with self.assertRaises(HevyError):
                HevyClient(
                    "synthetic-key", transport=lambda *_: response(payload)
                ).get_routine_payload("owned")

    @patch("integrations.hevy.urlopen")
    def test_real_transport_request_shapes_and_failures_without_network(self, open_url):
        returned = MagicMock()
        returned.__enter__.return_value = returned
        returned.status = 200
        returned.headers = {"X-Test": "synthetic"}
        returned.read.return_value = b"{}"
        open_url.return_value = returned
        self.assertEqual(
            default_transport(HevyClient.BASE_URL, {"api-key": "synthetic"}, 3)[0], 200
        )
        self.assertEqual(open_url.call_args.args[0].method, "GET")
        self.assertEqual(
            default_write_transport(
                HevyClient.BASE_URL, {"api-key": "synthetic"}, b"{}", 3, method="PUT"
            )[0],
            200,
        )
        self.assertEqual(open_url.call_args.args[0].method, "PUT")
        for transport, args in [
            (default_transport, ("https://api.hevyapp.com", {}, 3)),
            (default_write_transport, ("https://api.hevyapp.com", {}, b"{}", 3)),
        ]:
            open_url.side_effect = HTTPError(
                "https://api.hevyapp.com", 429, "limited", {}, BytesIO(b"{}")
            )
            self.assertEqual(transport(*args)[0], 429)
            open_url.side_effect = URLError("offline")
            with self.assertRaises(TimeoutError):
                transport(*args)
        self.assertIsNone(
            NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.test")
        )

    def test_json_response_limits_cached_pages_and_network_backoff(self):
        for body in [b"[]", b"bad", b"x" * (HevyClient.MAX_RESPONSE_BYTES + 1)]:
            with self.assertRaises(HevyError):
                HevyClient._decode_payload(body)
        client = HevyClient(
            "synthetic", transport=Mock(side_effect=OSError), sleep=lambda _: None
        )
        with self.assertRaises(HevyError):
            client._get("/v1/user/info")
        self.assertEqual(client.transport.call_count, 3)
        client.cached_catalog_pages = [
            {"page": 1, "page_count": 1, "exercise_templates": [template()]}
        ]
        self.assertEqual(
            client.pages("exercise_templates").items[0]["id"], "template-1"
        )
        with patch("integrations.hevy.build_opener") as opener:
            urlopen(Mock(), 3)
            opener.return_value.open.assert_called_once()


class ExportValidationTests(TestCase):
    def setUp(self):
        self.account = create_account()
        self.template = create_template(self.account)
        self.routine = create_routine(self.account, self.template)
        self.workout = create_workout(
            self.account, self.template, raw_payload=workout()
        )
        self.pages = [{"page": 1, "page_count": 1, "routines": [routine()]}]
        ProviderSnapshot.objects.create(
            hevy_account=self.account,
            resource="routines",
            pages=self.pages,
            synced_at=timezone.now(),
            source_hash="a" * 64,
        )
        self.client.force_login(self.account.user)

    def test_exports_keep_originals_and_canonical_units_with_owner_isolation(self):
        for kind in ["exercises", "routines", "workouts"]:
            result = self.client.get(
                reverse("integrations:local-export", args=[kind, "json"])
            )
            self.assertEqual(result.status_code, 200)
            self.assertIn("no-store", result["Cache-Control"])
            self.assertNotIn("api_key", result.content.decode())
        self.assertEqual(
            self.client.get(
                reverse("integrations:local-export", args=["routines", "json"])
            ).json()["pages"],
            self.pages,
        )
        for kind in ["exercises", "routines"]:
            result = self.client.get(
                reverse("integrations:local-export", args=[kind, "csv"])
            )
            self.assertGreater(
                len(list(csv.reader(StringIO(result.content.decode())))), 1
            )
        self.assertEqual(
            self.client.get(
                reverse("integrations:local-export", args=["unknown", "txt"])
            ).status_code,
            404,
        )
        other = create_account()
        self.client.force_login(other.user)
        self.assertEqual(
            self.client.get(
                reverse("integrations:local-export", args=["workouts", "json"])
            ).json()["workouts"],
            [],
        )

    def test_validator_numeric_shapes_and_modality_errors(self):
        validator = RoutinePayloadValidator(self.account)
        valid = example_payload(
            [{"id": self.template.external_id, "type": "weight_reps"}]
        )["operations"][0]["routine"]
        for field, value in [
            ("title", "x" * 256),
            ("folder_id", 999),
            ("exercises", [{}]),
        ]:
            with self.assertRaises(RoutineValidationError):
                validator.validate({"routine": {**valid, field: value}})
        for value in [True, -1, "notnumeric", 1.5, 1e200]:
            payload = copy.deepcopy(valid)
            payload["exercises"][0]["rest_seconds"] = value
            with self.assertRaises(RoutineValidationError):
                validator.validate({"routine": payload})
        for sets in [
            [],
            [{"type": "normal", "rep_range": {"start": None, "end": 2}}],
            [{"type": "normal", "notes": "x"}],
            [{"type": "unknown"}],
        ]:
            payload = copy.deepcopy(valid)
            payload["exercises"][0]["sets"] = sets
            with self.assertRaises(RoutineValidationError):
                validator.validate({"routine": payload})

    def test_interrupted_batch_is_recovered_as_unknown_without_provider_retry(self):
        SyncLock.objects.create(
            hevy_account=self.account,
            is_active=True,
            acquired_at=timezone.now() - timedelta(days=1),
        )
        proposal = RoutineProposal.objects.create(
            account=self.account,
            payload={},
            state="submitting",
            results=[
                {"state": "succeeded", "routine_id": "first"},
                {"state": "submitting"},
                {"state": "not_executed"},
            ],
            expires_at=timezone.now(),
        )
        IncrementalSyncService._acquire_lock(self.account)
        proposal.refresh_from_db()
        self.assertEqual(proposal.state, "unknown")
        self.assertEqual(
            [r["state"] for r in proposal.results],
            ["succeeded", "unknown", "not_executed"],
        )
        IncrementalSyncService._release_lock(self.account)

    def test_recovered_lock_fences_old_publication_and_release(self):
        from integrations.models import HevyAccount

        IncrementalSyncService._acquire_lock(self.account)
        newer = HevyAccount.objects.get(pk=self.account.pk)
        SyncLock.objects.filter(hevy_account=self.account).update(
            acquired_at=timezone.now() - timedelta(days=1)
        )
        IncrementalSyncService._acquire_lock(newer)
        with self.assertRaises(HevyError):
            IncrementalSyncService._assert_lock(self.account)
        IncrementalSyncService._release_lock(self.account)
        IncrementalSyncService._assert_lock(newer)
        IncrementalSyncService._release_lock(newer)
