"""Synthetic provider tests; no real Hevy writes or LLM requests."""

import copy
from datetime import datetime, timedelta
from datetime import timezone as dtz
from types import SimpleNamespace
from unittest.mock import Mock, patch

from cryptography.fernet import Fernet
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import DatabaseError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone, translation

from accounts.models import OwnerPreference
from dashboard.models import DashboardPreference
from dashboard.reports import PANELS, PreferenceForm, ReportForm, build_reports
from integrations.credentials import StoredCredentials, cipher, key_for_user
from integrations.dtos import payload_hash
from integrations.hevy import HevyError
from integrations.models import IntegrationState, ProviderSnapshot
from integrations.routines import RoutineValidationError
from integrations.services import FullImportService
from planning.forms import ImportForm, PromptForm
from planning.models import PromptGeneration, RoutineProposal, TrainingProfile
from planning.prompts import PLACEHOLDER, PromptBuilder, example_payload, json_text
from planning.proposals import (
    SecretInputError,
    parse_document,
    preview,
    submit,
    validate_envelope,
)
from training.models import ExerciseTemplate, Workout
from training.tests.factories import (
    create_account,
    create_routine,
    create_template,
    create_workout,
)

TEST_KEY = Fernet.generate_key().decode()


@override_settings(HEVY_ENCRYPTION_KEYS=TEST_KEY)
class PersistentCredentialTests(TestCase):
    def setUp(self):
        self.account = create_account()
        self.request = SimpleNamespace(user=self.account.user)
        self.store = StoredCredentials()

    def test_persistence_session_isolation_disconnect_and_rotation(self):
        self.store.put(self.request, "synthetic-canary-not-a-real-key")
        self.account.refresh_from_db()
        self.assertNotIn("synthetic-canary", self.account.encrypted_api_key)
        self.assertEqual(
            StoredCredentials().get(self.request), "synthetic-canary-not-a-real-key"
        )
        other = create_account()
        self.assertIsNone(key_for_user(other.user))
        self.client.force_login(self.account.user)
        self.client.post(reverse("accounts:logout"))
        self.assertEqual(
            key_for_user(self.account.user), "synthetic-canary-not-a-real-key"
        )
        new_key = Fernet.generate_key().decode()
        with override_settings(HEVY_ENCRYPTION_KEYS=new_key + "," + TEST_KEY):
            call_command("rotate_hevy_keys", verbosity=0)
        with override_settings(HEVY_ENCRYPTION_KEYS=new_key):
            self.assertEqual(
                key_for_user(self.account.user), "synthetic-canary-not-a-real-key"
            )
        self.store.delete(self.request)
        self.assertIsNone(key_for_user(self.account.user))
        self.assertTrue(type(self.account).objects.filter(pk=self.account.pk).exists())

    def test_safe_encryption_configuration_errors(self):
        for value in ["", "bad", "á"]:
            with (
                self.subTest(value=value),
                override_settings(HEVY_ENCRYPTION_KEYS=value),
                self.assertRaises(HevyError),
            ):
                cipher()
        self.store.put(self.request, "synthetic")
        with (
            override_settings(HEVY_ENCRYPTION_KEYS=Fernet.generate_key().decode()),
            self.assertRaises(HevyError),
        ):
            key_for_user(self.account.user)

    def test_connection_identity_cannot_mix_accounts(self):
        provider = Mock()
        provider.user_info.return_value = SimpleNamespace(
            external_id="different", name="Other", url=""
        )
        # Use the client contract rather than bypassing identity validation.
        from integrations.hevy import HevyClient

        provider = HevyClient(
            "synthetic",
            transport=lambda *_: (
                200,
                {},
                b'{"data":{"id":"different","name":"Other"}}',
            ),
        )
        with self.assertRaises(HevyError) as caught:
            FullImportService(provider).validate_account(self.account.user)
        self.assertEqual(caught.exception.code, "ACCOUNT_MISMATCH")
        self.account.refresh_from_db()
        self.assertNotEqual(self.account.external_user_id, "different")

    @patch("integrations.views.FullImportService.validate_account")
    def test_connect_logout_other_session_and_disconnect_http(self, validate):
        validate.return_value = self.account
        self.client.force_login(self.account.user)
        self.client.post(
            reverse("integrations:validate"), {"api_key": "synthetic-canary"}
        )
        second = Client()
        second.force_login(self.account.user)
        result = second.get(reverse("integrations:sync"))
        self.assertContains(result, "Update connection")
        self.assertNotContains(result, "synthetic-canary")
        second.post(reverse("integrations:disconnect"))
        self.assertIsNone(key_for_user(self.account.user))


class PlanningTests(TestCase):
    def setUp(self):
        self.account = create_account()
        self.template = create_template(self.account, external_id="synthetic-press")
        self.routine = create_routine(self.account, self.template)
        self.original = {
            "id": self.routine.external_id,
            "title": "Original",
            "notes": "Keep this full note",
            "extra_future_field": {"value": "preserved"},
            "exercises": [],
        }
        self.pages = [{"page": 1, "page_count": 1, "routines": [self.original]}]
        self.snapshot = ProviderSnapshot.objects.create(
            hevy_account=self.account,
            resource="routines",
            pages=self.pages,
            synced_at=timezone.now(),
            source_hash=payload_hash(self.pages),
        )
        self.workout = create_workout(
            self.account,
            self.template,
            raw_payload={
                "id": "synthetic-workout",
                "notes": "original workout note",
                "arbitrary_field": 42,
            },
        )
        self.inputs = {
            "period_mode": "last_28_days",
            "comments": "Keep rest periods",
            "objective": "Strength",
        }
        self.builder = PromptBuilder(self.account)
        self.envelope = example_payload(
            [{"id": self.template.external_id, "type": self.template.exercise_type}]
        )
        self.provider = Mock()
        self.provider.get_routine_payload.return_value = self.original
        self.provider.create_routine.return_value = SimpleNamespace(
            external_id="created"
        )
        self.provider.update_routine.return_value = SimpleNamespace(
            external_id=self.routine.external_id
        )
        self.client.force_login(self.account.user)

    def test_raw_fidelity_manifest_and_immutable_generation(self):
        text, manifest = self.builder.build(self.inputs)
        self.assertIn(json_text(self.pages), text)
        self.assertIn(json_text([self.workout.raw_payload]), text)
        self.assertIn(PLACEHOLDER, text)
        self.assertIn("one user message", text)
        generation = self.builder.save(self.inputs, text, manifest)
        self.snapshot.pages = []
        self.snapshot.save()
        generation.refresh_from_db()
        self.assertEqual(generation.text, text)
        with self.assertRaises(ValueError):
            generation.save()
        self.assertEqual(manifest["workout_count"], 1)
        self.assertEqual(manifest["routines_hash"], payload_hash(self.pages))
        self.assertEqual(manifest["bytes"], len(text.encode()))

    def test_all_modes_include_exact_local_boundaries_and_chronology(self):
        Workout.objects.all().delete()
        OwnerPreference.objects.create(
            user=self.account.user, presentation_timezone="America/Sao_Paulo"
        )
        frozen = datetime(2026, 3, 31, 14, tzinfo=dtz.utc)
        moments = [
            datetime(2026, 2, 28, 3, tzinfo=dtz.utc),
            datetime(2026, 3, 25, 2, 59, tzinfo=dtz.utc),
            datetime(2026, 3, 25, 3, tzinfo=dtz.utc),
            datetime(2026, 4, 1, 2, 59, tzinfo=dtz.utc),
            datetime(2026, 4, 1, 3, tzinfo=dtz.utc),
        ]
        for index, moment in enumerate(moments):
            create_workout(
                self.account,
                self.template,
                external_id=str(index),
                start_time=moment,
                end_time=moment + timedelta(minutes=30),
                raw_payload={"id": str(index)},
            )
        builder = PromptBuilder(self.account)
        with patch("planning.prompts.timezone.now", return_value=frozen):
            for mode, expected in [
                ("last_7_days", ["2", "3"]),
                ("last_month", ["0", "1", "2", "3"]),
                ("last_28_days", ["1", "2", "3"]),
            ]:
                _, manifest = builder.build({"period_mode": mode})
                self.assertEqual([w["id"] for w in manifest["workouts"]], expected)
            _, manifest = builder.build({"period_mode": "workouts", "count": 2})
            self.assertEqual([w["id"] for w in manifest["workouts"]], ["3", "4"])
            _, manifest = builder.build(
                {"period_mode": "custom", "start": "2026-03-25", "end": "2026-03-25"}
            )
            self.assertEqual([w["id"] for w in manifest["workouts"]], ["2"])
            with self.assertRaises(ValueError):
                builder.build(
                    {
                        "period_mode": "custom",
                        "start": "2026-04-01",
                        "end": "2026-03-01",
                    }
                )

    def test_missing_sources_and_explicit_operational_limits(self):
        with (
            patch("planning.prompts.MAX_PROMPT_BYTES", 10),
            self.assertRaisesMessage(ValueError, "no data was truncated"),
        ):
            self.builder.build(self.inputs)
        self.workout.raw_payload = {}
        self.workout.save()
        with self.assertRaisesMessage(ValueError, "original workout"):
            self.builder.build(self.inputs)
        self.workout.delete()
        text, manifest = self.builder.build(self.inputs)
        self.assertEqual(manifest["workout_count"], 0)
        self.snapshot.delete()
        with self.assertRaisesMessage(ValueError, "Synchronize routines"):
            self.builder.build(self.inputs)
        self.template.is_active = False
        self.template.save()
        with self.assertRaisesMessage(ValueError, "catalogue"):
            self.builder.build(self.inputs)

    def test_examples_use_the_import_validator_for_every_modality(self):
        for kind in ExerciseTemplate.ExerciseType.values:
            template = create_template(self.account, exercise_type=kind)
            payload = example_payload([{"id": template.external_id, "type": kind}])
            self.assertEqual(
                validate_envelope(self.account, payload)["schema_version"], 1
            )

    def test_parse_json_fences_duplicate_keys_nonfinite_and_secrets(self):
        text = json_text(self.envelope)
        self.assertEqual(parse_document(text), self.envelope)
        self.assertEqual(
            parse_document("Explanation.\n```json\n" + text + "\n```"), self.envelope
        )
        for text in [
            "[] ```json\n{}\n``` ```json\n{}\n```",
            '{"a":1,"a":2}',
            '{"a":NaN}',
            "[",
            "x" * 2_000_001,
        ]:
            with (
                self.subTest(text=text[:40]),
                self.assertRaises(RoutineValidationError),
            ):
                parse_document(text)
        for text in [
            '{"api_key":"secret-canary"}',
            '{"api-key":"secret-canary", BROKEN',
        ]:
            with self.assertRaises(SecretInputError):
                parse_document(text)

    def test_envelope_shapes_and_precise_paths(self):
        invalid = [
            None,
            {},
            {**self.envelope, "schema_version": True},
            {**self.envelope, "api_key": "secret"},
            {**self.envelope, "operations": []},
            {**self.envelope, "operations": [None]},
            {**self.envelope, "operations": [{"action": "delete"}]},
            {
                **self.envelope,
                "operations": [{"action": "create", "routine_id": "x", "routine": {}}],
            },
            {
                **self.envelope,
                "operations": [
                    {"action": "update", "routine_id": "foreign", "routine": {}}
                ],
            },
        ]
        for payload in invalid:
            with (
                self.subTest(payload=payload),
                self.assertRaises(RoutineValidationError),
            ):
                validate_envelope(self.account, payload)
        payload = copy.deepcopy(self.envelope)
        payload["operations"][0]["routine"]["exercises"][0]["superset_id"] = 0
        with self.assertRaisesMessage(RoutineValidationError, "superset"):
            validate_envelope(self.account, payload)
        payload["operations"][0]["routine"]["exercises"].append(
            copy.deepcopy(payload["operations"][0]["routine"]["exercises"][0])
        )
        self.assertEqual(
            len(
                validate_envelope(self.account, payload)["operations"][0]["routine"][
                    "exercises"
                ]
            ),
            2,
        )
        payload["operations"][0]["routine"]["exercises"][0]["sets"][0]["rpe"] = 8
        with self.assertRaisesMessage(
            RoutineValidationError, "operations[0].routine.exercises[0].sets[0]"
        ):
            validate_envelope(self.account, payload)

    def update_envelope(self):
        payload = copy.deepcopy(self.envelope)
        payload["operations"][0].update(
            action="update", routine_id=self.routine.external_id
        )
        return payload

    @patch("planning.proposals.PlanRefreshService.run")
    def test_update_and_create_batch_success_and_duplicate_confirmation(self, refresh):
        payload = self.update_envelope()
        payload["operations"].append(self.envelope["operations"][0])
        proposal = preview(self.account, payload, self.provider)
        self.provider.create_routine.assert_not_called()
        result = submit(self.account, proposal.pk, self.provider)
        self.assertEqual(result.state, "succeeded")
        self.assertEqual(
            [r["state"] for r in result.results], ["succeeded", "succeeded"]
        )
        self.assertFalse(result.local_refresh_pending)
        self.provider.update_routine.assert_called_once()
        self.assertEqual(
            self.provider.update_routine.call_args.args[0], self.routine.external_id
        )
        self.assertEqual(
            set(self.provider.update_routine.call_args.args[1]), {"routine"}
        )
        with self.assertRaises(RoutineValidationError):
            submit(self.account, proposal.pk, self.provider)
        self.provider.create_routine.assert_called_once()

    def test_expiry_and_external_conflict_do_not_write(self):
        proposal = preview(self.account, self.update_envelope(), self.provider)
        self.provider.get_routine_payload.return_value = {
            "id": self.routine.external_id,
            "title": "external edit",
        }
        self.assertEqual(
            submit(self.account, proposal.pk, self.provider).state, "conflict"
        )
        proposal = preview(self.account, self.envelope, self.provider)
        RoutineProposal.objects.filter(pk=proposal.pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        self.assertEqual(
            submit(self.account, proposal.pk, self.provider).state, "expired"
        )
        self.provider.create_routine.assert_not_called()
        self.provider.update_routine.assert_not_called()

    @patch("planning.proposals.PlanRefreshService.run", side_effect=DatabaseError)
    def test_partial_unknown_never_retries_and_remote_success_local_failure(
        self, refresh
    ):
        payload = copy.deepcopy(self.envelope)
        payload["operations"] *= 3
        proposal = preview(self.account, payload, self.provider)
        self.provider.create_routine.side_effect = [
            SimpleNamespace(external_id="first"),
            HevyError("WRITE_UNKNOWN", "unknown"),
        ]
        result = submit(self.account, proposal.pk, self.provider)
        self.assertEqual(result.state, "unknown")
        self.assertEqual(
            [r["state"] for r in result.results],
            ["succeeded", "unknown", "not_executed"],
        )
        self.assertTrue(result.local_refresh_pending)
        self.assertEqual(self.provider.create_routine.call_count, 2)
        with self.assertRaises(RoutineValidationError):
            submit(self.account, proposal.pk, self.provider)
        self.assertEqual(self.provider.create_routine.call_count, 2)

    def test_permanent_and_revalidation_failure_results(self):
        proposal = preview(self.account, self.envelope, self.provider)
        self.provider.create_routine.side_effect = HevyError("AUTH_INVALID", "rejected")
        result = submit(self.account, proposal.pk, self.provider)
        self.assertEqual(result.state, "failed")
        self.assertEqual(result.results[0]["code"], "AUTH_INVALID")
        proposal = preview(self.account, self.update_envelope(), self.provider)
        self.provider.get_routine_payload.side_effect = HevyError(
            "HTTP_TRANSIENT", "unavailable"
        )
        self.assertEqual(
            submit(self.account, proposal.pk, self.provider).state, "failed"
        )

    def test_profile_and_prompt_forms_progressive_validation(self):
        for data in [
            {"period_mode": "workouts"},
            {"period_mode": "custom"},
            {"period_mode": "custom", "start": "2026-02-02", "end": "2026-01-01"},
            {"period_mode": "last_28_days", "session_minutes": 1},
            {"period_mode": "last_28_days", "objective": "a" * 2001},
        ]:
            self.assertFalse(PromptForm(data).is_valid())
        form = PromptForm(
            {
                "period_mode": "last_28_days",
                "count": "7",
                "start": "2020-01-01",
                "end": "2021-01-01",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data["count"])
        self.assertIsNone(form.cleaned_data["start"])
        for data, files in [
            ({}, {}),
            ({"payload": "{}"}, {"file": SimpleUploadedFile("a.json", b"{}")}),
            ({}, {"file": SimpleUploadedFile("a.json", b"\xff")}),
            ({}, {"file": SimpleUploadedFile("a.json", b"x" * 2_000_001)}),
        ]:
            self.assertFalse(ImportForm(data, files).is_valid())
        form = ImportForm({}, {"file": SimpleUploadedFile("a.json", b"{}")})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["payload"], "{}")

    def test_saved_generation_http_preview_download_duplicate_delete_and_isolation(
        self,
    ):
        response = self.client.post(reverse("planning:generate"), self.inputs)
        self.assertEqual(response.status_code, 200)
        signature = response.context["signature"]
        result = self.client.post(
            reverse("planning:generate"),
            {**self.inputs, "action": "save", "signature": signature},
        )
        generation = PromptGeneration.objects.get()
        self.assertRedirects(
            result, reverse("planning:generation", args=[generation.pk])
        )
        detail = self.client.get(result.url)
        self.assertContains(detail, "original workout note")
        self.assertEqual(
            self.client.get(result.url + "?download=1")["Content-Type"],
            "text/markdown; charset=utf-8",
        )
        self.assertContains(
            self.client.get(reverse("planning:generations")), "Saved prompt"
        )
        duplicate = self.client.get(
            reverse("planning:generate"), {"duplicate": generation.pk}
        )
        self.assertEqual(
            duplicate.context["form"].initial["comments"], self.inputs["comments"]
        )
        self.assertEqual(
            self.client.get(
                reverse("planning:generate"), {"duplicate": "bad"}
            ).status_code,
            404,
        )
        other = Client()
        other.force_login(create_account().user)
        self.assertEqual(other.get(result.url).status_code, 404)
        self.assertEqual(other.post(result.url, {"confirm": "delete"}).status_code, 404)
        self.assertContains(self.client.post(result.url, {}), "Confirm deletion")
        self.client.post(result.url, {"confirm": "delete"})
        self.assertFalse(PromptGeneration.objects.exists())
        self.assertTrue(Workout.objects.exists())
        response = self.client.post(
            reverse("planning:generate"),
            {**self.inputs, "action": "save", "signature": "bad"},
        )
        self.assertContains(response, "preview changed or expired")

    @patch("planning.views._client_for_request")
    def test_import_http_clears_keys_preserves_invalid_json_and_scopes_confirmation(
        self, factory
    ):
        factory.return_value = self.provider
        url = reverse("planning:import")
        self.assertContains(self.client.get(url), "Import routine JSON")
        result = self.client.post(url, {"payload": '{"api_key":"CANARY-PRIVATE"}'})
        self.assertNotContains(result, "CANARY-PRIVATE")
        self.assertContains(result, "document was cleared")
        result = self.client.post(url, {"payload": "BROKEN-CONTEXT"})
        self.assertContains(result, "BROKEN-CONTEXT")
        result = self.client.post(url, {"payload": json_text(self.envelope)})
        proposal = RoutineProposal.objects.get()
        self.assertRedirects(result, reverse("planning:proposal", args=[proposal.pk]))
        self.assertContains(self.client.get(result.url), "Confirm and apply")
        other = Client()
        other.force_login(create_account().user)
        self.assertEqual(other.post(result.url, {"confirm": "apply"}).status_code, 404)
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.account.user)
        self.assertEqual(csrf.post(result.url, {"confirm": "apply"}).status_code, 403)
        with patch("planning.proposals.PlanRefreshService.run"):
            self.client.post(result.url, {"confirm": "apply"})
        self.assertContains(self.client.get(result.url), "Results by operation")
        self.client.post(result.url, {"confirm": "apply"})
        self.provider.create_routine.assert_called_once()

    def test_profile_http_and_no_account_paths(self):
        url = reverse("planning:profile")
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertRedirects(
            self.client.post(url, {"objective": "Stronger", "session_minutes": 45}), url
        )
        self.assertEqual(TrainingProfile.objects.get().objective, "Stronger")
        self.assertEqual(self.client.post(url, {"session_minutes": 1}).status_code, 200)
        Workout.objects.all().delete()
        type(self.routine).objects.all().delete()
        self.account.delete()
        self.assertContains(
            self.client.post(reverse("planning:generate"), self.inputs), "Connect Hevy"
        )
        self.assertContains(
            self.client.post(reverse("planning:import"), {"payload": "{}"}),
            "Connect Hevy",
        )

    def test_reports_all_panels_filters_saved_preferences_and_units(self):
        OwnerPreference.objects.create(
            user=self.account.user,
            mass_unit="lb",
            distance_unit="mi",
            weekly_session_target=3,
        )
        for key, _ in PANELS:
            with self.subTest(panel=key):
                response = self.client.get(
                    reverse("dashboard:reports"),
                    {"panel": key, "exercise": self.template.pk, "compare": "on"},
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Data table and definition")
        report = build_reports(self.account, {"exercise": self.template}, "progression")
        load = next(c for c in report["charts"] if c["dom_id"] == "exercise-weight_kg")
        self.assertEqual(load["unit"], "lb")
        self.assertIn("93.7", load["table_rows"][0]["value"])
        result = self.client.post(
            reverse("dashboard:reports"),
            {
                "panels": ["effort", "frequency"],
                "position_1": "frequency",
                "position_2": "effort",
                "favorites": [self.template.pk],
            },
        )
        self.assertEqual(result.status_code, 302)
        pref = DashboardPreference.objects.get(user=self.account.user)
        self.assertEqual(pref.panels, ["frequency", "effort"])
        self.assertEqual(list(pref.favorites.all()), [self.template])
        self.assertEqual(
            self.client.post(
                reverse("dashboard:reports"),
                {
                    "action": "save_filters",
                    "exercise": self.template.pk,
                    "compare": "on",
                },
            ).status_code,
            302,
        )
        pref.refresh_from_db()
        self.assertEqual(pref.filters["exercise"], str(self.template.pk))
        self.assertEqual(self.client.get(reverse("dashboard:reports")).status_code, 200)
        for data in [
            {"start": "2026-02-01", "end": "2026-01-01"},
            {"exercise": 999999},
        ]:
            self.assertFalse(ReportForm(data, account=self.account).is_valid())
        self.assertFalse(PreferenceForm({"position_1": "effort", "position_2": "effort"}).is_valid())
        self.assertFalse(PreferenceForm({"position_1": "alien"}).is_valid())
        self.assertEqual(
            self.client.get(
                reverse("dashboard:reports"), {"panel": "unknown"}
            ).status_code,
            200,
        )


@override_settings(HEVY_ENCRYPTION_KEYS=TEST_KEY)
class AutomaticSyncTests(TestCase):
    def setUp(self):
        self.account = create_account()
        self.client.force_login(self.account.user)
        self.url = reverse("integrations:automatic")
        StoredCredentials().put(
            SimpleNamespace(user=self.account.user), "synthetic-canary"
        )

    @patch("integrations.automatic.FullImportService.run")
    def test_initial_import_reserved_and_manual_fallback(self, full):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        result = self.client.post(self.url, HTTP_ACCEPT="application/json")
        self.assertEqual(result.json()["status"], "updated")
        full.assert_called_once()
        result = self.client.post(self.url, HTTP_ACCEPT="application/json")
        self.assertEqual(result.json()["status"], "current")
        full.assert_called_once()
        self.assertEqual(self.client.post(self.url).status_code, 302)

    @patch("integrations.automatic.HevyClient")
    @patch("integrations.automatic.IncrementalSyncService.run")
    @patch("integrations.automatic.PlanRefreshService.run")
    def test_stale_plans_use_daily_catalog_cache_and_incremental(
        self, plans, incremental, client
    ):
        now = timezone.now()
        IntegrationState.objects.filter(hevy_account=self.account).update(
            last_full_refresh_at=now, last_catalog_at=now
        )
        ProviderSnapshot.objects.create(
            hevy_account=self.account,
            resource="exercise_templates",
            pages=[{"page": 1, "page_count": 1, "exercise_templates": []}],
            synced_at=now,
            source_hash="a" * 64,
        )
        self.assertEqual(
            self.client.post(self.url, HTTP_ACCEPT="application/json").json()["status"],
            "updated",
        )
        self.assertIsInstance(client.return_value.cached_catalog_pages, list)
        plans.assert_called_once()
        incremental.assert_called_once()
        IntegrationState.objects.filter(hevy_account=self.account).update(
            last_plans_at=now, last_incremental_run_at=now, next_auto_attempt_at=None
        )
        self.client.post(self.url, HTTP_ACCEPT="application/json")
        plans.assert_called_once()
        self.client.post(self.url, {"manual": "1"}, HTTP_ACCEPT="application/json")
        self.assertEqual(plans.call_count, 2)

    @patch(
        "integrations.automatic.FullImportService.run",
        side_effect=HevyError("HTTP_TRANSIENT", "unavailable"),
    )
    def test_failed_sync_preserves_data_and_backs_off(self, full):
        workout = create_workout(self.account)
        self.assertEqual(
            self.client.post(self.url, HTTP_ACCEPT="application/json").status_code, 503
        )
        self.assertTrue(Workout.objects.filter(pk=workout.pk).exists())
        self.assertEqual(
            self.client.post(self.url, HTTP_ACCEPT="application/json").json()["status"],
            "current",
        )
        StoredCredentials().delete(SimpleNamespace(user=self.account.user))
        self.assertEqual(
            self.client.post(self.url, HTTP_ACCEPT="application/json").json()["status"],
            "disconnected",
        )


class LocalizationContractTests(TestCase):
    def test_native_cookie_stable_urls_and_unit_independence(self):
        account = create_account()
        template = create_template(
            account, title="Bench Press (Barbell)", title_pt_br="Supino reto (barra)"
        )
        create_workout(account, template)
        OwnerPreference.objects.create(
            user=account.user, mass_unit="lb", date_format="MDY"
        )
        self.client.force_login(account.user)
        result = self.client.post(
            reverse("set_language"), {"language": "pt-br", "next": "/dashboard/"}
        )
        self.assertEqual(result.url, "/dashboard/")
        self.assertEqual(result.cookies["django_language"].value, "pt-br")
        self.assertContains(self.client.get("/dashboard/"), "Visão geral")
        self.assertContains(
            self.client.get("/exercises/", {"q": "Supino"}), "Supino reto"
        )
        self.client.cookies["django_language"] = "en"
        self.assertContains(self.client.get("/exercises/"), "Bench Press (Barbell)")
        self.assertContains(self.client.get("/dashboard/"), "Overview")

    def test_display_names_preserve_custom_and_unknown(self):
        from training.translations import display_name

        account = create_account()
        template = create_template(account, title_pt_br="Revisado")
        with translation.override("pt-br"):
            self.assertEqual(display_name(template), "Revisado")
            template.is_custom = True
            self.assertEqual(display_name(template), template.title)


class MalformedImportTests(TestCase):
    def test_unhashable_action_and_type_are_validation_errors(self):
        account = create_account()
        template = create_template(account)
        envelope = example_payload(
            [{"id": template.external_id, "type": "weight_reps"}]
        )
        envelope["operations"][0]["action"] = []
        with self.assertRaises(RoutineValidationError):
            validate_envelope(account, envelope)
        envelope["operations"][0]["action"] = "create"
        envelope["operations"][0]["routine"]["exercises"][0]["sets"][0]["type"] = []
        with self.assertRaises(RoutineValidationError):
            validate_envelope(account, envelope)

    def test_secret_is_cleared_even_when_form_has_another_error(self):
        account = create_account()
        self.client.force_login(account.user)
        response = self.client.post(
            reverse("planning:import"),
            {
                "payload": '{"api_key":"CANARY-PRIVATE"}',
                "file": SimpleUploadedFile("a.json", b"{}"),
            },
        )
        self.assertNotContains(response, "CANARY-PRIVATE")
        self.assertContains(response, "document was cleared")


class PreparedModalityTests(TestCase):
    def test_overview_preparation_uses_each_modality_without_mixing_units(self):
        from analytics.preparation import HistoryPreparationService
        from analytics.services import AnalyticsService

        account = create_account()
        for kind, unit in [
            ("weight_reps", "kg"),
            ("weight_duration", "kg"),
            ("bodyweight_assisted_reps", "kg"),
            ("reps_only", "repetitions"),
            ("bodyweight_reps", "repetitions"),
            ("distance_duration", "km"),
            ("short_distance_weight", "km"),
            ("duration", "s"),
            ("custom", "custom units"),
        ]:
            template = create_template(account, exercise_type=kind)
            workout = create_workout(account, template)
            item = workout.exercises.get().sets.get()
            item.duration_seconds = 30
            item.distance_meters = 100
            item.custom_metric = 2
            item.save()
            prepared = HistoryPreparationService(
                account, AnalyticsService(account).period(), exercise=template
            ).build()
            self.assertEqual(prepared["exercise_evolution_unit"], unit)
            self.assertEqual(len(prepared["exercise_evolution"]), 1)
            item.set_type = "warmup"
            item.save()
            empty = HistoryPreparationService(
                account, AnalyticsService(account).period(), exercise=template
            ).build()
            self.assertFalse(empty["exercise_evolution"])

    def test_monthly_frequency_and_disclosure(self):
        account = create_account()
        create_workout(account)
        self.client.force_login(account.user)
        response = self.client.get(
            reverse("dashboard:reports"), {"panel": "frequency", "grouping": "month"}
        )
        self.assertContains(response, "Workouts per month")
        self.assertContains(response, "id_grouping")
        response = self.client.get(
            reverse("dashboard:reports"), {"panel": "effort", "grouping": "month"}
        )
        self.assertNotContains(response, "id_grouping")


class ProgressiveFormTests(TestCase):
    def test_irrelevant_malformed_fields_are_discarded_before_validation(self):
        form = PromptForm(
            {
                "period_mode": "last_28_days",
                "count": "bad",
                "start": "bad",
                "end": "bad",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data["count"])
        form = PromptForm(
            data={"period_mode": "workouts", "count": "bad", "start": "bad"}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("count", form.errors)
        self.assertNotIn("start", form.errors)


class EscapedSecretTests(TestCase):
    def test_encoded_json_key_is_rejected_before_form_errors_can_echo_it(self):
        encoded = '{"api' + chr(92) + 'u005fkey":"SYNTHETIC-CANARY"}'
        with self.assertRaises(SecretInputError):
            parse_document(encoded)
