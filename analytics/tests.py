from datetime import date, datetime
from datetime import timezone as dt_timezone
from decimal import Decimal

from django.test import TestCase

from accounts.models import OwnerPreference
from analytics.services import AnalyticsService, local_period
from training.models import ExerciseSecondaryMuscle, SetType, WorkoutSet
from training.tests.factories import create_account, create_template, create_workout


class AnalyticsMetricTests(TestCase):
    def setUp(self):
        self.account = create_account()
        self.template = create_template(self.account)
        self.service = AnalyticsService(self.account)

    def test_local_period_is_inclusive_and_timezone_aware(self):
        period = local_period(
            timezone_name="America/Sao_Paulo",
            start=date(2026, 1, 1),
            end=date(2026, 1, 3),
        )
        self.assertEqual(period.days, 3)
        self.assertEqual(period.start_at.isoformat(), "2026-01-01T00:00:00-03:00")
        self.assertEqual(period.end_at.isoformat(), "2026-01-04T00:00:00-03:00")

    def test_period_rejects_reversed_and_naive_datetime_bounds(self):
        with self.assertRaises(ValueError):
            local_period(
                timezone_name="UTC", start=date(2026, 1, 2), end=date(2026, 1, 1)
            )
        with self.assertRaises(ValueError):
            local_period(
                timezone_name="UTC", start=datetime(2026, 1, 1), end=date(2026, 1, 2)
            )
        with self.assertRaises(ValueError):
            local_period(timezone_name="Invalid/Zone")
        aware = datetime(2026, 1, 2, 23, tzinfo=dt_timezone.utc)
        self.assertEqual(
            local_period(timezone_name="UTC", start=aware, end=aware).days, 1
        )

    def test_activity_duration_and_set_metrics(self):
        create_workout(
            self.account,
            self.template,
            start_time=datetime(2026, 1, 2, 12, tzinfo=dt_timezone.utc),
            end_time=datetime(2026, 1, 2, 13, tzinfo=dt_timezone.utc),
        )
        period = self.service.period(date(2026, 1, 1), date(2026, 1, 3))
        activity = self.service.workout_activity(period)
        self.assertEqual(activity["workouts"].value, 1)
        self.assertEqual(activity["training_days"].value, 1)
        self.assertEqual(
            self.service.duration_metrics(period).value["total_seconds"],
            Decimal("3600"),
        )
        sets = self.service.set_metrics(period)
        self.assertEqual(sets["working_sets"].value, 1)
        self.assertEqual(sets["external_load_volume"].value, Decimal("340.000"))

    def test_null_values_are_not_zero_and_warmups_are_not_working(self):
        workout = create_workout(
            self.account,
            self.template,
            start_time=datetime(2026, 1, 2, 12, tzinfo=dt_timezone.utc),
            end_time=datetime(2026, 1, 2, 13, tzinfo=dt_timezone.utc),
        )
        recorded = workout.exercises.get().sets.get()
        recorded.reps = None
        recorded.weight_kg = None
        recorded.save()
        WorkoutSet.objects.create(
            workout_exercise=workout.exercises.get(),
            position=1,
            set_type=SetType.WARMUP,
            weight_kg=Decimal("20"),
            reps=Decimal("5"),
        )
        metrics = self.service.set_metrics(
            self.service.period(date(2026, 1, 1), date(2026, 1, 3))
        )
        self.assertEqual(metrics["repetitions"].value, Decimal("5.000"))
        self.assertEqual(metrics["repetitions"].missing_value_count, 1)
        self.assertEqual(metrics["working_sets"].value, 0)

    def test_zero_duration_remains_zero_and_valid(self):
        create_workout(
            self.account,
            self.template,
            start_time=datetime(2026, 1, 2, 12, tzinfo=dt_timezone.utc),
            end_time=datetime(2026, 1, 2, 12, tzinfo=dt_timezone.utc),
        )

        result = self.service.duration_metrics(
            self.service.period(date(2026, 1, 1), date(2026, 1, 3))
        )

        self.assertEqual(result.value["total_seconds"], Decimal("0"))
        self.assertEqual(result.value["average_seconds"], Decimal("0.00"))
        self.assertEqual(result.missing_value_count, 0)
        self.assertTrue(result.is_valid)

    def test_rpe_records_and_estimated_one_rm(self):
        workout = create_workout(
            self.account,
            self.template,
            start_time=datetime(2026, 1, 2, 12, tzinfo=dt_timezone.utc),
            end_time=datetime(2026, 1, 2, 13, tzinfo=dt_timezone.utc),
        )
        WorkoutSet.objects.create(
            workout_exercise=workout.exercises.get(),
            position=1,
            set_type=SetType.FAILURE,
            weight_kg=Decimal("100"),
            reps=Decimal("5"),
            rpe=Decimal("9"),
        )
        period = self.service.period(date(2026, 1, 1), date(2026, 1, 3))
        rpe = self.service.rpe_metrics(period)
        self.assertEqual(rpe["mean"].value, Decimal("8.75"))
        self.assertEqual(rpe["missing"].value["count"], 0)
        records = self.service.records(self.template, period)
        self.assertEqual(records["maximum_load"], Decimal("100.000"))
        self.assertAlmostEqual(
            records["estimated_1rm"], Decimal("116.6666666666666666666666666667")
        )
        self.assertTrue(records["estimated_1rm_is_estimate"])

    def test_estimated_one_rm_excludes_fractional_and_high_rep_sets(self):
        workout = create_workout(
            self.account,
            self.template,
            start_time=datetime(2026, 1, 2, 12, tzinfo=dt_timezone.utc),
            end_time=datetime(2026, 1, 2, 13, tzinfo=dt_timezone.utc),
        )
        original = workout.exercises.get().sets.get()
        original.reps = Decimal("11")
        original.save()
        WorkoutSet.objects.create(
            workout_exercise=workout.exercises.get(),
            position=1,
            set_type=SetType.NORMAL,
            weight_kg=Decimal("100"),
            reps=Decimal("5.5"),
        )

        records = self.service.records(
            self.template,
            self.service.period(date(2026, 1, 1), date(2026, 1, 3)),
        )

        self.assertIsNone(records["estimated_1rm"])
        self.assertEqual(records["eligible_set_count"], 1)

    def test_modality_and_muscles_remain_separate(self):
        duration = create_template(
            self.account,
            external_id="duration",
            exercise_type="duration",
            primary_muscle="cardio",
        )
        ExerciseSecondaryMuscle.objects.create(
            exercise_template=self.template, muscle_code="triceps"
        )
        create_workout(
            self.account,
            self.template,
            start_time=datetime(2026, 1, 2, 12, tzinfo=dt_timezone.utc),
            end_time=datetime(2026, 1, 2, 13, tzinfo=dt_timezone.utc),
        )
        duration_workout = create_workout(
            self.account,
            duration,
            start_time=datetime(2026, 1, 2, 14, tzinfo=dt_timezone.utc),
            end_time=datetime(2026, 1, 2, 15, tzinfo=dt_timezone.utc),
        )
        set_row = duration_workout.exercises.get().sets.get()
        set_row.weight_kg = None
        set_row.reps = None
        set_row.duration_seconds = Decimal("60")
        set_row.save()
        period = self.service.period(date(2026, 1, 1), date(2026, 1, 3))
        modalities = self.service.modality_metrics(period)
        self.assertEqual(modalities["duration"]["duration_total"], Decimal("60"))
        muscles = self.service.muscle_distribution(period)
        self.assertEqual(muscles["executed_primary"].value["chest"], 1)
        self.assertEqual(muscles["executed_secondary"].value["triceps"], 1)

    def test_comparison_and_target_metadata(self):
        self.assertIsNone(self.service.weekly_target_consistency().value)
        OwnerPreference.objects.update_or_create(
            user=self.account.user, defaults={"weekly_session_target": 2}
        )
        result = self.service.compare_periods(
            lambda period: self.service.workout_activity(period)["workouts"],
            self.service.period(date(2026, 1, 8), date(2026, 1, 14)),
            self.service.period(date(2026, 1, 1), date(2026, 1, 7)),
        )
        self.assertEqual(result["validity"], "valid")
        self.assertIsNone(result["percent"])
        self.assertIsNone(self.service.trend_slope([(0, 1)]))
        self.assertEqual(self.service.trend_slope([(1, 2), (1, 4)]), Decimal("0.00"))

    def test_weekly_target_uses_sessions_and_excludes_partial_weeks(self):
        OwnerPreference.objects.update_or_create(
            user=self.account.user, defaults={"weekly_session_target": 2}
        )
        for index, count in enumerate((2, 1, 3)):
            for session in range(count):
                start = datetime(
                    2026, 1, 5 + index * 7 + session, 12, tzinfo=dt_timezone.utc
                )
                create_workout(
                    self.account,
                    self.template,
                    start_time=start,
                    end_time=start.replace(hour=13),
                )
        result = self.service.weekly_target_consistency(
            self.service.period(date(2026, 1, 5), date(2026, 1, 25))
        )
        self.assertEqual(result.value["completed_sessions"], 6)
        self.assertEqual(result.value["target_sessions"], 6)
        self.assertEqual(result.value["completed_weeks"], 2)

    def test_metric_helpers_trends_and_streaks_cover_boundary_paths(self):
        OwnerPreference.objects.update_or_create(
            user=self.account.user,
            defaults={"weekly_session_target": 1},
        )
        for week in range(4):
            start = datetime(2026, 1, 5 + week * 7, 12, tzinfo=dt_timezone.utc)
            create_workout(
                self.account,
                self.template,
                start_time=start,
                end_time=start.replace(hour=13),
            )
        period = self.service.period(date(2026, 1, 5), date(2026, 2, 1))

        self.assertEqual(
            self.service.activity_buckets(period, bucket="month").unit, "workouts/month"
        )
        with self.assertRaises(ValueError):
            self.service.activity_buckets(period, bucket="day")
        self.assertEqual(
            self.service.repetition_metrics(period).value, Decimal("32.000")
        )
        self.assertEqual(self.service.working_set_definition(period).value, 4)
        self.assertEqual(
            self.service.e1rm(self.template, period),
            Decimal("53.83333333333333333333333335"),
        )
        self.assertTrue(
            self.service.primary_secondary_muscles(period)["executed_primary"].is_valid
        )
        self.assertEqual(
            self.service.frequency_duration_trend(period)["validity"], "valid"
        )
        self.assertEqual(self.service.streaks(period)["activity"], 4)
        self.assertEqual(self.service.streaks(period)["target"], 4)
        self.assertTrue(
            self.service.workout_activity(period)["workouts"].as_dict()["is_valid"]
        )


class ReportComparisonTests(TestCase):
    def setUp(self):
        from datetime import timedelta

        self.account = create_account()
        self.template = create_template(self.account, primary_muscle="chest")
        self.filters = {
            "start": date(2026, 8, 17),
            "end": date(2026, 8, 30),
            "compare": True,
        }
        self.workouts = []
        for day, weight, reps, effort in [
            (10, "40", 10, "7"),
            (18, "50", 8, "8"),
            (25, "60", 5, None),
        ]:
            start = datetime(2026, 8, day, 12, tzinfo=dt_timezone.utc)
            workout = create_workout(
                self.account,
                self.template,
                start_time=start,
                end_time=start + timedelta(minutes=45),
            )
            item = workout.exercises.get().sets.get()
            item.weight_kg = Decimal(weight)
            item.reps = reps
            item.rpe = Decimal(effort) if effort else None
            item.save()
            self.workouts.append(workout)

    def report(self, panel, **extra):
        from analytics.reporting import build_report_data

        return build_report_data(self.account, {**self.filters, **extra}, panel)

    def test_comparisons_use_equal_periods_full_data_and_eligible_units(self):
        from accounts.templatetags.fitness_units import POUNDS_PER_KILOGRAM
        from dashboard.reports import build_reports

        OwnerPreference.objects.create(user=self.account.user, mass_unit="lb")
        data = build_reports(
            self.account, {**self.filters, "exercise": self.template}, "progression"
        )
        by_name = {m["name"]: m for m in data["comparisons"]}
        volume = by_name["Exercise volume"]
        self.assertEqual(volume["unit"], "lb·rep")
        self.assertEqual(volume["current"], Decimal(700) * POUNDS_PER_KILOGRAM)
        self.assertEqual(volume["previous"], Decimal(400) * POUNDS_PER_KILOGRAM)
        self.assertEqual(volume["percent"], 75)
        records = {r["name"]: r for r in data["records"]}
        self.assertEqual(
            records["Estimated 1RM"]["value"], Decimal(70) * POUNDS_PER_KILOGRAM
        )
        self.assertIn("25/08/2026", records["Estimated 1RM"]["date"])
        self.assertEqual(
            self.report("duration")["scalars"]["duration-total"]["value"], 90
        )
        self.assertEqual(
            self.report("duration")["scalars"]["duration-mean"]["value"], 45
        )
        self.assertEqual(self.report("effort")["scalars"]["rpe"]["value"], 8)

    def test_missing_rpe_and_empty_previous_period_are_not_zero_measurements(self):
        data = self.report("effort", start=date(2026, 8, 25), end=date(2026, 8, 25))
        rpe = next(m for m in data["comparisons"] if m["name"] == "Mean RPE")
        self.assertIsNone(rpe["current"])
        self.assertIsNone(rpe["absolute"])
        self.assertIsNone(rpe["percent"])
        sessions = next(m for m in data["comparisons"] if m["name"] == "Workouts")
        self.assertEqual(sessions["previous"], 0)
        self.assertIsNone(sessions["percent"])
        self.assertEqual(data["rpe_coverage"].value["count"], 1)

    def test_weekly_target_partial_weeks_empty_weeks_and_muscle_filter(self):
        OwnerPreference.objects.create(user=self.account.user, weekly_session_target=2)
        data = self.report("frequency", start=date(2026, 8, 18), end=date(2026, 9, 6))
        target = next(c for c in data["charts"] if c["dom_id"] == "frequency-target")
        self.assertEqual(list(target["values"].values()), [1, 1, 0])
        self.assertEqual(target["target"], 2)
        self.assertEqual(target["partial_keys"], [date(2026, 8, 17)])
        from dashboard.reports import build_reports

        rendered = build_reports(
            self.account,
            {**self.filters, "start": date(2026, 8, 18), "end": date(2026, 9, 6)},
            "frequency",
        )
        rendered_target = next(
            c for c in rendered["charts"] if c["dom_id"] == "frequency-target"
        )
        self.assertIn("Partial", rendered_target["table_rows"][0]["label"])
        self.assertNotIn("Partial", rendered_target["table_rows"][1]["label"])
        target_metric = next(
            m for m in data["summary_metrics"] if m.metric_id == "M-C01"
        )
        self.assertEqual(target_metric.value["complete_weeks"], 2)
        self.assertEqual(target_metric.value["completed_sessions"], 1)
        distribution = self.report("distribution", muscle="chest")
        weekly = next(
            c for c in distribution["charts"] if c["dom_id"] == "muscle-weekly"
        )
        self.assertEqual(sum(weekly["values"].values()), 2)
        self.assertEqual(
            self.report("distribution", muscle="biceps")["scalars"]["working_sets"][
                "value"
            ],
            0,
        )

    def test_foreign_accounts_and_unselected_exercises_are_excluded(self):
        other = create_account()
        create_workout(
            other,
            start_time=self.workouts[1].start_time,
            end_time=self.workouts[1].end_time,
        )
        self.assertEqual(self.report("volume")["scalars"]["sessions"]["value"], 2)
        self.assertEqual(self.report("progression")["records"], [])
        self.assertTrue(self.report("progression")["needs_exercise"])
        data = self.report("progression", exercise=self.template, equipment="dumbbell")
        self.assertEqual(data["scalars"]["sessions"]["value"], 0)

    def test_e1rm_excludes_warmups_high_reps_and_incompatible_modalities(self):
        item = self.workouts[1].exercises.get().sets.get()
        item.reps = 11
        item.save()
        item = self.workouts[2].exercises.get().sets.get()
        item.set_type = "warmup"
        item.save()
        data = self.report("progression", exercise=self.template)
        self.assertIsNone(data["scalars"]["exercise-e1rm"]["value"])
        self.template.exercise_type = "bodyweight_assisted_reps"
        self.template.save()
        data = self.report("progression", exercise=self.template)
        self.assertNotIn("exercise-e1rm", data["scalars"])
        self.assertNotIn("exercise-volume", data["scalars"])

    def test_record_ties_keep_earliest_session_and_date_labels_hide_ids(self):
        from dashboard.reports import build_reports

        item = self.workouts[2].exercises.get().sets.get()
        item.weight_kg = Decimal(50)
        item.save()
        data = build_reports(
            self.account, {**self.filters, "exercise": self.template}, "progression"
        )
        record = next(
            r for r in data["records"] if r["name"] == "Recorded load / assistance"
        )
        self.assertIn("18/08/2026", record["date"])
        chart = next(c for c in data["charts"] if c["dom_id"] == "exercise-weight_kg")
        self.assertTrue(all(" · " not in row["label"] for row in chart["table_rows"]))

    def test_same_load_trend_requires_repeated_sessions_and_keeps_original_records(
        self,
    ):
        data = self.report("progression", exercise=self.template)
        self.assertFalse(
            any(c["dom_id"].startswith("load-reps-") for c in data["charts"])
        )
        item = self.workouts[-1].exercises.get().sets.get()
        item.weight_kg = Decimal(50)
        item.save()
        data = self.report("progression", exercise=self.template)
        repeated = [c for c in data["charts"] if c["dom_id"].startswith("load-reps-")]
        self.assertEqual(len(repeated), 1)
        self.assertEqual(list(repeated[0]["values"].values()), [8, 5])
