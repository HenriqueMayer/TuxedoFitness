"""Refresh only local display fields; never contact or rewrite provider data."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from training.models import ExerciseTemplate
from training.translations import CATALOG_VERSION, translated_title


class Command(BaseCommand):
    help = "Apply the reviewed PT-BR catalogue to existing standard exercises."

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            action="store_true",
            help="Report coverage without writing; fail if updates or unknown standard exercises remain.",
        )

    def handle(self, *args, **options):
        pending, unknown = [], set()
        with transaction.atomic():
            for exercise in ExerciseTemplate.all_objects.filter(
                is_custom=False
            ).iterator():
                name = translated_title(
                    exercise.title, external_id=exercise.external_id
                )
                if not name:
                    unknown.add((exercise.external_id, exercise.title))
                    continue
                if (
                    exercise.title_pt_br != name
                    or exercise.translation_version != CATALOG_VERSION
                ):
                    exercise.title_pt_br = name
                    exercise.translation_version = CATALOG_VERSION
                    pending.append(exercise)
            if not options["check"]:
                ExerciseTemplate.all_objects.bulk_update(
                    pending, ["title_pt_br", "translation_version"], batch_size=250
                )
        self.stdout.write(
            f"{len(pending)} updates {'required' if options['check'] else 'applied'}; {len(unknown)} unknown standard exercises."
        )
        for identifier, title in sorted(unknown):
            self.stdout.write(f"Unmapped: {identifier} — {title}")
        if options["check"] and (pending or unknown):
            raise CommandError("Catalogue coverage requires attention.")
