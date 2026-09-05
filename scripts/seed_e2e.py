"""Populate only the runner's disposable installation with synthetic records."""

import os
from datetime import timedelta
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()


def main():
    from django.conf import settings
    from django.utils import timezone

    from accounts.models import OwnerPreference
    from integrations.dtos import payload_hash
    from integrations.models import ProviderSnapshot
    from planning.models import TrainingProfile
    from training.tests.factories import (
        create_account,
        create_routine,
        create_template,
        create_workout,
    )
    from training.translations import CATALOG_VERSION, REVIEWED_TITLES

    root = Path(os.environ["FITNESS_SYNTHETIC_ROOT"]).resolve()
    database = Path(settings.DATABASES["default"]["NAME"]).resolve()
    if (
        not root.name.startswith("tuxedo-e2e-")
        or root not in database.parents
        or settings.BASE_DIR in database.parents
    ):
        raise RuntimeError(
            "Synthetic data requires the isolated runner temporary database."
        )
    account = create_account("e2e-owner")
    account.user.set_password(os.environ["E2E_PASSWORD"])
    account.user.save(update_fields=["password"])
    OwnerPreference.objects.create(user=account.user, weekly_session_target=3)
    TrainingProfile.objects.create(
        user=account.user,
        objective="Build consistent strength",
        available_days="Monday, Wednesday, Friday",
        session_minutes=60,
        equipment="Barbell, dumbbells, cable",
    )
    templates = []
    for index, title in enumerate(list(REVIEWED_TITLES)[:60]):
        templates.append(
            create_template(
                account,
                external_id=f"synthetic-exercise-{index}",
                title=title,
                title_pt_br=REVIEWED_TITLES[title],
                translation_version=CATALOG_VERSION,
            )
        )
    routine = create_routine(
        account,
        templates[0],
        external_id="synthetic-routine",
        title="Upper · strength and control",
    )
    original = {
        "id": routine.external_id,
        "title": routine.title,
        "folder_id": routine.folder.external_id,
        "notes": "Synthetic prescription only.",
        "exercises": [
            {
                "index": 0,
                "title": templates[0].title,
                "exercise_template_id": templates[0].external_id,
                "superset_id": None,
                "rest_seconds": 90,
                "notes": "Controlled tempo",
                "sets": [
                    {
                        "index": 0,
                        "type": "normal",
                        "weight_kg": None,
                        "reps": None,
                        "rep_range": {"start": 8, "end": 12},
                    }
                ],
            }
        ],
    }
    routine.raw_payload = original
    routine.save(update_fields=["raw_payload"])
    pages = [{"page": 1, "page_count": 1, "routines": [original]}]
    ProviderSnapshot.objects.create(
        hevy_account=account,
        resource="routines",
        pages=pages,
        synced_at=timezone.now(),
        source_hash=payload_hash(pages),
    )
    now = timezone.now()
    for index in range(56):
        start = now - timedelta(days=index * 2, hours=1)
        template = templates[index % 3]
        raw = {
            "id": f"synthetic-workout-{index}",
            "title": f"Strength session {56 - index:02d}",
            "start_time": start.isoformat(),
            "end_time": (start + timedelta(minutes=50)).isoformat(),
            "routine_id": routine.external_id,
            "description": "Synthetic training history.",
            "exercises": [
                {
                    "index": 0,
                    "title": template.title,
                    "exercise_template_id": template.external_id,
                    "notes": "Stable technique",
                    "superset_id": None,
                    "sets": [
                        {
                            "index": 0,
                            "type": "normal",
                            "weight_kg": 40 + index % 8 * 2.5,
                            "reps": 8,
                            "rpe": None if index % 4 == 0 else 8,
                        }
                    ],
                }
            ],
        }
        workout = create_workout(
            account,
            template,
            routine=routine,
            title=raw["title"],
            external_id=raw["id"],
            start_time=start,
            end_time=start + timedelta(minutes=50),
            raw_payload=raw,
            source_payload_hash=payload_hash(raw),
        )
        training_set = workout.exercises.get().sets.get()
        training_set.weight_kg = raw["exercises"][0]["sets"][0]["weight_kg"]
        training_set.rpe = raw["exercises"][0]["sets"][0]["rpe"]
        training_set.save()


if __name__ == "__main__":
    main()
