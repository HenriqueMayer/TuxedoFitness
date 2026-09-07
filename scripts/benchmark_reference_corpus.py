#!/usr/bin/env python3
"""Measure warm local requests against the synthetic PRD reference corpus."""

from __future__ import annotations

import json
import math
import os
import sys
import tempfile
import time
from datetime import timedelta
from decimal import Decimal
from pathlib import Path


def percentile_95(values):
    return sorted(values)[math.ceil(len(values) * 0.95) - 1]


def measure(client, url, samples=20):
    warm = client.get(url)
    if warm.status_code != 200:
        raise RuntimeError(f"Warm request failed for {url}: {warm.status_code}")
    durations = []
    size = 0
    for _ in range(samples):
        started = time.perf_counter()
        response = client.get(url)
        durations.append(time.perf_counter() - started)
        if response.status_code != 200:
            raise RuntimeError(f"Request failed for {url}: {response.status_code}")
        size = len(response.content)
    return {"p95_seconds": percentile_95(durations), "response_bytes": size}


def run(database_path):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    env_file = database_path.parent / ".env"
    env_file.touch(mode=0o600)
    os.environ["TUXEDO_ENV_FILE"] = str(env_file)
    os.environ["TUXEDO_DATA_DIR"] = str(database_path.parent)
    os.environ["SECRET_KEY"] = "synthetic-reference-corpus-only"
    os.environ["HTTPS"] = "False"
    os.environ["ALLOWED_HOSTS"] = "testserver"
    os.environ["HEVY_API_KEY"] = ""
    os.environ["HEVY_ENCRYPTION_KEYS"] = ""
    os.environ["TUXEDO_FITNESS_DB"] = str(database_path)
    os.environ["DEBUG"] = "False"

    import django

    django.setup()

    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.test import Client
    from django.urls import reverse
    from django.utils import timezone

    from integrations.models import HevyAccount, IntegrationState
    from training.models import (
        ExerciseTemplate,
        SetType,
        Workout,
        WorkoutExercise,
        WorkoutSet,
    )

    call_command("migrate", verbosity=0)
    user = get_user_model().objects.create_user("benchmark-owner")
    account = HevyAccount.objects.create(
        user=user,
        external_user_id="benchmark-owner",
        display_name="Synthetic Benchmark Owner",
        verified_at=timezone.now(),
    )
    IntegrationState.objects.create(
        hevy_account=account,
        status=IntegrationState.Status.CONNECTED,
        is_stale=False,
    )
    now = timezone.now()
    synchronized = {
        "synced_at": now,
        "provider_schema_version": "benchmark-v1",
        "source_payload_hash": "a" * 64,
    }
    ExerciseTemplate.all_objects.bulk_create(
        [
            ExerciseTemplate(
                hevy_account=account,
                external_id=f"exercise-{index:03d}",
                title=f"Exercise {index:03d}",
                exercise_type=ExerciseTemplate.ExerciseType.WEIGHT_REPS,
                equipment_category=ExerciseTemplate.EquipmentCategory.BARBELL,
                primary_muscle=ExerciseTemplate.MuscleGroup.CHEST,
                **synchronized,
            )
            for index in range(100)
        ]
    )
    template_ids = list(
        ExerciseTemplate.all_objects.filter(hevy_account=account)
        .order_by("pk")
        .values_list("pk", flat=True)
    )
    Workout.all_objects.bulk_create(
        [
            Workout(
                hevy_account=account,
                external_id=f"workout-{index:05d}",
                title=f"Workout {index:05d}",
                start_time=now - timedelta(days=index % 3650, minutes=index % 1440),
                end_time=now
                - timedelta(days=index % 3650, minutes=index % 1440)
                + timedelta(hours=1),
                **synchronized,
            )
            for index in range(10_000)
        ],
        batch_size=1_000,
    )
    workout_ids = (
        Workout.all_objects.filter(hevy_account=account)
        .order_by("pk")
        .values_list("pk", flat=True)
    )
    WorkoutExercise.objects.bulk_create(
        [
            WorkoutExercise(
                workout_id=workout_id,
                position=0,
                exercise_template_id=template_ids[index % len(template_ids)],
                title_snapshot=f"Exercise {index % len(template_ids):03d}",
            )
            for index, workout_id in enumerate(workout_ids)
        ],
        batch_size=2_000,
    )
    exercise_ids = WorkoutExercise.objects.order_by("pk").values_list("pk", flat=True)
    pending = []
    for exercise_id in exercise_ids:
        pending.extend(
            WorkoutSet(
                workout_exercise_id=exercise_id,
                position=position,
                set_type=SetType.NORMAL,
                weight_kg=Decimal("75.000"),
                reps=Decimal("8.000"),
                rpe=Decimal("8.0"),
            )
            for position in range(20)
        )
        if len(pending) >= 10_000:
            WorkoutSet.objects.bulk_create(pending, batch_size=2_000)
            pending.clear()
    if pending:
        WorkoutSet.objects.bulk_create(pending, batch_size=2_000)

    client = Client()
    client.force_login(user)
    history_url = f"{reverse('training:history')}?set_type=normal"
    results = {
        "corpus": {"workouts": 10_000, "workout_sets": 200_000},
        "dashboard": measure(client, reverse("dashboard:index")),
        "history_filter": measure(client, history_url),
        "exercise_filter": measure(
            client,
            f"{reverse('training:exercises')}?q=Exercise",
        ),
        "reports": {
            panel: measure(
                client,
                reverse("dashboard:reports")
                + f"?panel={panel}"
                + (f"&exercise={template_ids[0]}" if panel == "progression" else ""),
            )
            for panel in [
                "frequency",
                "progression",
                "effort",
                "volume",
                "distribution",
                "duration",
            ]
        },
        "reports_comparison": {
            panel: measure(
                client,
                reverse("dashboard:reports")
                + f"?panel={panel}&compare=on"
                + (f"&exercise={template_ids[0]}" if panel == "progression" else ""),
            )
            for panel in ["progression", "volume", "distribution"]
        },
        "targets_seconds": {"dashboard": 1.5, "filters": 1.0},
        "page_size_limit_bytes": 1_572_864,
    }
    results["passed"] = (
        all(
            result["p95_seconds"] <= 1.5 and result["response_bytes"] <= 1_572_864
            for result in [
                *results["reports"].values(),
                *results["reports_comparison"].values(),
            ]
        )
        and results["dashboard"]["p95_seconds"] <= 1.5
        and results["history_filter"]["p95_seconds"] <= 1.0
        and results["exercise_filter"]["p95_seconds"] <= 1.0
        and all(
            results[key]["response_bytes"] <= 1_572_864
            for key in ("dashboard", "history_filter", "exercise_filter")
        )
    )
    print(json.dumps(results, indent=2))
    return 0 if results["passed"] else 1


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="tuxedo-fitness-benchmark-") as directory:
        raise SystemExit(run(Path(directory) / "benchmark.sqlite3"))
