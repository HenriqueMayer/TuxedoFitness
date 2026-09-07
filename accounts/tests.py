import os
import shutil
import sqlite3
import tempfile
from datetime import timedelta
from io import StringIO
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import OwnerPreference
from accounts.services import (
    BackupError,
    create_verified_backup,
    prune_private_snapshots,
    prune_sync_runs,
    sqlite_checks,
)
from accounts.templatetags.fitness_units import (
    display_distance,
    display_duration,
    display_mass,
    display_volume,
)
from integrations.models import SyncRun
from training.tests.factories import create_account, create_workout


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="owner",
            password="Strong-local-password-274",
        )

    def test_login_uses_native_authentication(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "owner", "password": "Strong-local-password-274"},
        )

        self.assertRedirects(response, reverse("dashboard:index"))

    def test_logout_rejects_get_and_accepts_post(self):
        self.client.force_login(self.user)

        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        response = self.client.post(reverse("accounts:logout"))

        self.assertRedirects(response, reverse("pages:landing"))

    def test_logout_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)

        response = client.post(reverse("accounts:logout"))

        self.assertEqual(response.status_code, 403)

    def test_login_requires_and_accepts_csrf(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse("accounts:login"), {}).status_code, 403)
        client.get(reverse("accounts:login"))
        token = client.cookies["csrftoken"].value

        response = client.post(
            reverse("accounts:login"),
            {
                "username": "owner",
                "password": "Strong-local-password-274",
                "csrfmiddlewaretoken": token,
            },
        )

        self.assertRedirects(response, reverse("dashboard:index"))

    @override_settings(SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True)
    def test_authentication_cookies_use_secure_attributes(self):
        login_page = self.client.get(reverse("accounts:login"), secure=True)
        csrf = login_page.cookies["csrftoken"]
        self.assertTrue(csrf["secure"])
        self.assertEqual(csrf["samesite"], "Lax")

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "owner", "password": "Strong-local-password-274"},
            secure=True,
        )

        session = response.cookies["sessionid"]
        self.assertTrue(session["secure"])
        self.assertTrue(session["httponly"])
        self.assertEqual(session["samesite"], "Lax")


class SignupTests(TestCase):
    @override_settings(ALLOW_SIGNUPS=True)
    def test_login_offers_registration_when_available(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertContains(response, "Create account")
        self.assertContains(response, reverse("accounts:signup"))

    @override_settings(ALLOW_SIGNUPS=True)
    def test_user_can_register_and_is_logged_in(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "new-owner",
                "email": "owner@example.test",
                "password1": "Strong-local-password-274",
                "password2": "Strong-local-password-274",
            },
        )

        self.assertRedirects(response, reverse("dashboard:index"))
        user = get_user_model().objects.get(username="new-owner")
        self.assertTrue(OwnerPreference.objects.filter(user=user).exists())
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    @override_settings(ALLOW_SIGNUPS=True)
    def test_registration_remains_available_for_another_user(self):
        get_user_model().objects.create_user("existing-owner")

        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "second-user",
                "email": "second@example.test",
                "password1": "Strong-local-password-274",
                "password2": "Strong-local-password-274",
            },
        )

        self.assertRedirects(response, reverse("dashboard:index"))
        self.assertTrue(
            get_user_model().objects.filter(username="second-user").exists()
        )

    @override_settings(ALLOW_SIGNUPS=False)
    def test_registration_can_be_disabled_by_environment(self):
        response = self.client.get(reverse("accounts:signup"))

        self.assertEqual(response.status_code, 403)
        self.assertContains(
            response, "Registration is disabled for this installation.", status_code=403
        )


class OwnerPreferenceTests(TestCase):
    def test_defaults_match_the_mvp_presentation_baseline(self):
        user = get_user_model().objects.create_user("preferences")
        preference = OwnerPreference.objects.create(user=user)

        self.assertEqual(preference.presentation_timezone, "America/Sao_Paulo")
        self.assertIsNone(preference.weekly_session_target)
        self.assertEqual(preference.mass_unit, "kg")
        self.assertEqual(preference.distance_unit, "km")
        self.assertEqual(preference.snapshot_retention_days, 7)

    def test_settings_reads_existing_preferences_without_mutating_them(self):
        user = get_user_model().objects.create_user("settings-owner")
        OwnerPreference.objects.create(user=user)
        self.client.force_login(user)
        before = OwnerPreference.objects.count()

        response = self.client.get(reverse("accounts:settings"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "America/Sao_Paulo")
        self.assertEqual(OwnerPreference.objects.count(), before)

    def test_settings_updates_local_preferences(self):
        user = get_user_model().objects.create_user("settings-edit-owner")
        OwnerPreference.objects.create(user=user)
        self.client.force_login(user)

        response = self.client.post(
            reverse("accounts:settings"),
            {
                "presentation_timezone": "UTC",
                "date_format": "DMY",
                "weekly_session_target": "4",
                "mass_unit": "lb",
                "distance_unit": "mi",
                "snapshot_retention_days": "21",
            },
        )

        self.assertRedirects(response, reverse("accounts:settings"))
        preference = OwnerPreference.objects.get(user=user)
        self.assertEqual(preference.presentation_timezone, "UTC")
        self.assertEqual(preference.weekly_session_target, 4)
        self.assertEqual(preference.mass_unit, "lb")
        self.assertEqual(preference.distance_unit, "mi")
        self.assertEqual(preference.snapshot_retention_days, 21)

    def test_settings_mutation_requires_csrf(self):
        user = get_user_model().objects.create_user("settings-csrf-owner")
        OwnerPreference.objects.create(user=user)
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)

        response = client.post(
            reverse("accounts:settings"),
            {
                "presentation_timezone": "UTC",
                "date_format": "DMY",
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_settings_rejects_unknown_timezone(self):
        user = get_user_model().objects.create_user("settings-invalid-owner")
        OwnerPreference.objects.create(user=user)
        self.client.force_login(user)

        response = self.client.post(
            reverse("accounts:settings"),
            {
                "presentation_timezone": "Not/A_Timezone",
                "weekly_session_target": "",
                "mass_unit": "kg",
                "distance_unit": "km",
                "snapshot_retention_days": "7",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "valid IANA timezone")

    def test_settings_rejects_snapshot_retention_above_limit(self):
        user = get_user_model().objects.create_user("settings-retention-owner")
        preference = OwnerPreference.objects.create(user=user)
        self.client.force_login(user)

        response = self.client.post(
            reverse("accounts:settings"),
            {
                "presentation_timezone": "UTC",
                "date_format": "DMY",
                "weekly_session_target": "",
                "mass_unit": "kg",
                "distance_unit": "km",
                "snapshot_retention_days": "31",
            },
        )

        self.assertEqual(response.status_code, 200)
        preference.refresh_from_db()
        self.assertEqual(preference.snapshot_retention_days, 7)

    @mock.patch(
        "accounts.views.create_verified_backup",
        return_value=Path("/tmp/synthetic-backup.sqlite3"),
    )
    def test_delete_requires_confirmation_and_verified_backup(self, backup):
        account = create_account("settings-delete-owner")
        create_workout(account)
        self.client.force_login(account.user)

        response = self.client.post(
            reverse("accounts:settings"),
            {
                "action": "delete_data",
                "confirmation": "EXCLUIR",
            },
        )

        self.assertRedirects(response, reverse("accounts:settings"))
        backup.assert_called_once_with()
        self.assertFalse(type(account).objects.filter(pk=account.pk).exists())

    @mock.patch("accounts.views.create_verified_backup")
    def test_delete_without_confirmation_does_not_backup(self, backup):
        account = create_account("settings-no-confirm-owner")
        self.client.force_login(account.user)

        self.client.post(
            reverse("accounts:settings"),
            {
                "action": "delete_data",
                "confirmation": "apagar",
            },
        )

        backup.assert_not_called()
        self.assertTrue(type(account).objects.filter(pk=account.pk).exists())

    @mock.patch(
        "accounts.views.create_verified_backup",
        side_effect=BackupError("Backup unavailable."),
    )
    def test_delete_stops_when_backup_fails(self, backup):
        account = create_account("settings-backup-failure-owner")
        self.client.force_login(account.user)

        self.client.post(
            reverse("accounts:settings"),
            {
                "action": "delete_data",
                "confirmation": "EXCLUIR",
            },
        )

        backup.assert_called_once_with()
        self.assertTrue(type(account).objects.filter(pk=account.pk).exists())


class BackupServiceTests(TransactionTestCase):
    def test_backup_is_created_outside_checkout_and_passes_integrity(self):
        with (
            tempfile.TemporaryDirectory() as backup_dir,
            mock.patch.dict(os.environ, {"TUXEDO_FITNESS_BACKUP_DIR": backup_dir}),
        ):
            backup = create_verified_backup()

            self.assertTrue(backup.is_file())
            self.assertEqual(backup.parent, Path(backup_dir))
            with sqlite3.connect(backup) as connection:
                self.assertEqual(
                    connection.execute("PRAGMA integrity_check").fetchone()[0], "ok"
                )
                self.assertEqual(
                    connection.execute("PRAGMA foreign_key_check").fetchall(), []
                )

    def test_isolated_restore_copy_passes_database_checks(self):
        with (
            tempfile.TemporaryDirectory() as backup_dir,
            tempfile.TemporaryDirectory() as restore_dir,
            mock.patch.dict(os.environ, {"TUXEDO_FITNESS_BACKUP_DIR": backup_dir}),
        ):
            backup = create_verified_backup()
            restored = Path(restore_dir) / "restored.sqlite3"
            shutil.copy2(backup, restored)

            self.assertEqual(sqlite_checks(restored), ("ok", ()))

    def test_backup_and_check_commands_report_verified_database(self):
        output = StringIO()
        with (
            tempfile.TemporaryDirectory() as backup_dir,
            mock.patch.dict(os.environ, {"TUXEDO_FITNESS_BACKUP_DIR": backup_dir}),
        ):
            call_command("backup_database", stdout=output)
            backup = next(Path(backup_dir).glob("*.sqlite3"))
            call_command("check_database", "--database", str(backup), stdout=output)

        self.assertIn("Backup verified:", output.getvalue())
        self.assertIn("integrity_check=ok", output.getvalue())
        self.assertIn("foreign_key_check=ok", output.getvalue())

    def test_database_check_rejects_a_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.sqlite3"
            with self.assertRaises(CommandError) as error:
                call_command("check_database", "--database", str(missing))

        self.assertEqual(error.exception.returncode, 6)
        self.assertFalse(missing.exists())


class CreateOwnerCommandTests(TestCase):
    def test_command_creates_one_regular_owner_and_preferences(self):
        output = StringIO()
        environment = {"TUXEDO_OWNER_PASSWORD": "Strong-local-password-274"}

        with mock.patch.dict(os.environ, environment):
            call_command(
                "create_owner",
                "local-owner",
                "--no-input",
                stdout=output,
            )

        user = get_user_model().objects.get(username="local-owner")
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password(environment["TUXEDO_OWNER_PASSWORD"]))
        self.assertTrue(OwnerPreference.objects.filter(user=user).exists())
        self.assertIn("Proprietário local-owner criado.", output.getvalue())

    def test_command_refuses_a_second_owner(self):
        get_user_model().objects.create_user("existing-owner")

        with self.assertRaisesMessage(CommandError, "A local owner already exists."):
            call_command("create_owner", "second-owner", "--no-input")


class RuntimeRetentionTests(TestCase):
    def test_snapshot_retention_only_removes_expired_private_json_files(self):
        now = timezone.now()
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(DATA_DIR=Path(directory)),
        ):
            snapshots = Path(directory) / "hevy-snapshots"
            snapshots.mkdir()
            expired = snapshots / "expired.json"
            current = snapshots / "current.json"
            ignored = snapshots / "notes.txt"
            for path in (expired, current, ignored):
                path.touch()
            os.utime(expired, (now.timestamp() - 8 * 86400,) * 2)
            os.utime(current, (now.timestamp() - 86400,) * 2)

            removed = prune_private_snapshots(7, now=now)

            self.assertEqual(removed, 1)
            self.assertFalse(expired.exists())
            self.assertTrue(current.exists())
            self.assertTrue(ignored.exists())

    def test_sync_run_retention_keeps_the_latest_twenty_per_account(self):
        account = create_account("retention-owner")
        now = timezone.now()
        for index in range(25):
            run = SyncRun.objects.create(
                hevy_account=account,
                mode=SyncRun.Mode.FULL,
                trigger=SyncRun.Trigger.COMMAND,
            )
            SyncRun.objects.filter(pk=run.pk).update(
                created_at=now - timedelta(days=230 - index)
            )

        removed = prune_sync_runs(now=now)

        self.assertEqual(removed, 5)
        self.assertEqual(SyncRun.objects.filter(hevy_account=account).count(), 20)

    def test_retention_command_uses_the_owner_snapshot_preference(self):
        user = get_user_model().objects.create_user("retention-command-owner")
        OwnerPreference.objects.create(user=user, snapshot_retention_days=0)
        output = StringIO()
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(DATA_DIR=Path(directory)),
        ):
            snapshots = Path(directory) / "hevy-snapshots"
            snapshots.mkdir()
            snapshot = snapshots / "current.json"
            snapshot.touch()

            call_command("prune_runtime_data", stdout=output)

            self.assertFalse(snapshot.exists())
        self.assertIn("snapshots=1", output.getvalue())


class PresentationUnitTests(TestCase):
    def test_mass_volume_and_distance_follow_presentation_units(self):
        self.assertEqual(display_mass("42.5", "lb"), "93.70 lb")
        self.assertEqual(display_volume("340", "lb"), "749.57 lb·rep")
        self.assertEqual(display_distance("5000", "mi"), "3.11 mi")
        self.assertEqual(display_distance("5000", "km"), "5.00 km")

    def test_invalid_presentation_value_is_not_coerced_to_zero(self):
        self.assertEqual(display_mass(None), "—")
        self.assertEqual(display_duration(None), "—")
        self.assertEqual(display_duration(42000), "11 h 40 min")
        self.assertEqual(display_duration("60.1"), "1 min")
        self.assertEqual(display_duration(0), "0 s")
        self.assertEqual(display_distance("invalid"), "—")


class NavigationQueryTests(TestCase):
    def test_query_links_replace_values_instead_of_accumulating_them(self):
        from django.test import RequestFactory

        from accounts.templatetags.fitness_ui import querystring

        request = RequestFactory().get("/dashboard/reports/?panel=effort&page=2")
        self.assertEqual(
            querystring({"request": request}, panel="volume", page=None), "panel=volume"
        )
        self.assertEqual(request.GET["page"], "2")
