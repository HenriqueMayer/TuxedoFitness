import io

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import translation

from training.tests.factories import create_account, create_template
from training.translations import (
    CATALOG,
    CATALOG_VERSION,
    display_name,
    translated_title,
)


class CatalogueTests(TestCase):
    def test_all_standard_entries_have_reviewed_id_bound_translations(self):
        self.assertEqual(len(CATALOG), 451)
        for identifier, entry in CATALOG.items():
            with self.subTest(identifier=identifier):
                self.assertTrue(entry["pt_BR"].strip())
                self.assertEqual(
                    translated_title(entry["title"], external_id=identifier),
                    entry["pt_BR"],
                )
                self.assertEqual(
                    translated_title("Renamed exercise", external_id=identifier), ""
                )
                self.assertEqual(translated_title(entry["title"], True, identifier), "")
        self.assertEqual(translated_title("Plank", external_id="unknown"), "")

    def test_existing_data_refresh_is_idempotent_and_originals_are_unchanged(self):
        account = create_account()
        entry = next(iter(CATALOG.values()))
        template = create_template(
            account,
            external_id=entry["id"],
            title=entry["title"],
            raw_payload={"title": entry["title"]},
        )
        custom = create_template(
            account, external_id="custom-id", title="Meu movimento", is_custom=True
        )
        original = {
            key: value
            for key, value in type(template)
            .all_objects.filter(pk=template.pk)
            .values()
            .get()
            .items()
            if key not in {"_state", "title_pt_br", "translation_version"}
        }
        with self.assertRaises(CommandError):
            call_command("translate_exercises", check=True, stdout=io.StringIO())
        template.refresh_from_db()
        self.assertEqual(template.title_pt_br, "")
        call_command("translate_exercises", stdout=io.StringIO())
        call_command("translate_exercises", check=True, stdout=io.StringIO())
        template.refresh_from_db()
        custom.refresh_from_db()
        self.assertEqual(template.title_pt_br, entry["pt_BR"])
        self.assertEqual(template.translation_version, CATALOG_VERSION)
        self.assertEqual(custom.title_pt_br, "")
        self.assertEqual(
            original,
            {
                key: value
                for key, value in type(template)
                .all_objects.filter(pk=template.pk)
                .values()
                .get()
                .items()
                if key not in {"_state", "title_pt_br", "translation_version"}
            },
        )
        with translation.override("pt-br"):
            self.assertEqual(display_name(template), entry["pt_BR"])
            self.assertEqual(display_name(custom), "Meu movimento")
        with translation.override("en"):
            self.assertEqual(display_name(template), entry["title"])
        out = io.StringIO()
        call_command("translate_exercises", stdout=out)
        self.assertIn("0 updates applied", out.getvalue())

    def test_unknown_standard_name_is_reported_and_preserved(self):
        template = create_template(
            create_account(),
            external_id="unknown",
            title="Unmapped",
            title_pt_br="Previous label",
        )
        out = io.StringIO()
        with self.assertRaises(CommandError):
            call_command("translate_exercises", check=True, stdout=out)
        self.assertIn("Unmapped: unknown", out.getvalue())
        call_command("translate_exercises", stdout=io.StringIO())
        template.refresh_from_db()
        self.assertEqual(template.title_pt_br, "Previous label")
