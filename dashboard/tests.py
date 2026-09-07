from datetime import date

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from analytics.services import local_period
from core.assets import frontend_version, versioned_static
from dashboard.presenters import DashboardPresenter
from training.tests.factories import create_account, create_template, create_workout


class ProtectedShellTests(TestCase):
    protected_routes = [
        "dashboard:index",
        "training:history",
        "training:exercises",
        "training:routines",
        "integrations:sync",
        "accounts:settings",
    ]

    def test_personal_routes_require_authentication(self):
        for route in self.protected_routes:
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertRedirects(
                    response,
                    f"{reverse('accounts:login')}?next={reverse(route)}",
                )

    def test_shell_has_matching_desktop_and_mobile_destinations(self):
        user = get_user_model().objects.create_user("shell-owner")
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard:index"))

        self.assertContains(response, 'role="dialog"')
        self.assertContains(response, 'id="mobile-menu"')
        self.assertContains(response, "inert")
        html = response.content.decode()
        for route in self.protected_routes:
            self.assertGreaterEqual(html.count(f'href="{reverse(route)}"'), 2)

    def test_shell_assets_are_local_and_csp_blocks_inline_code(self):
        user = get_user_model().objects.create_user("asset-owner")
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard:index"))
        html = response.content.decode()
        policy = response.headers["Content-Security-Policy"]

        self.assertIn(versioned_static("css/app.css"), html)
        self.assertIn("/static/brand/tuxedo-fitness-emblem-128.png", html)
        self.assertIn("/static/js/htmx-2.0.10.min.js", html)
        self.assertIn("/static/js/navigation.js", html)
        self.assertIn("/static/js/mobile-menu.js", html)
        self.assertIn('hx-boost="true"', html)
        self.assertIn('"includeIndicatorStyles":false', html)
        self.assertNotIn("https://", html)
        self.assertNotIn("'unsafe-inline'", policy)

    def test_dashboard_renders_confirmed_local_metrics(self):
        account = create_account("dashboard-owner")
        create_workout(account)
        self.client.force_login(account.user)

        response = self.client.get(reverse("dashboard:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Overview")
        self.assertContains(response, "Workouts")

    def test_dashboard_accepts_reproducible_date_query(self):
        account = create_account("period-owner")
        create_workout(account)
        self.client.force_login(account.user)

        response = self.client.get(
            reverse("dashboard:index"),
            {"start": "2026-01-01", "end": "2026-01-03"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "01/01/2026 – 03/01/2026")

    def test_dashboard_query_count_stays_bounded(self):
        account = create_account("query-owner")
        create_workout(account)
        self.client.force_login(account.user)

        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("dashboard:index"))

        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(queries), 50)

    def test_dashboard_comparison_is_opt_in(self):
        account = create_account("comparison-owner")
        create_workout(account)
        self.client.force_login(account.user)

        response = self.client.get(reverse("dashboard:index"), {"compare": "on"})

        self.assertContains(response, "Comparison:")

    def test_dashboard_query_count_with_reference_corpus(self):
        account = create_account("corpus-owner")
        template = create_template(account)
        for index in range(100):
            create_workout(account, template, external_id=f"corpus-{index}")
        self.client.force_login(account.user)

        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("dashboard:index"))

        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(queries), 50)

    def test_dashboard_exposes_server_svg_and_equivalent_table(self):
        account = create_account("chart-owner")
        create_workout(account, create_template(account))
        self.client.force_login(account.user)

        response = self.client.get(reverse("dashboard:index"))

        self.assertContains(response, "<svg")
        self.assertContains(response, '<title id="activity-chart-title">')
        self.assertContains(response, '<desc id="activity-chart-desc">')
        self.assertNotContains(response, "plotly", html=False)
        self.assertNotContains(response, "application/json")
        self.assertContains(response, "Data table and definition")
        self.assertContains(
            response, 'aria-labelledby="activity-chart-title activity-chart-desc"'
        )

    def test_dashboard_chart_is_safe_and_no_data_is_explicit(self):
        account = create_account("empty-chart-owner")
        self.client.force_login(account.user)

        response = self.client.get(
            reverse("dashboard:index"),
            {
                "start": "2030-01-01",
                "end": "2030-01-28",
            },
        )

        self.assertNotContains(response, "activity-chart-title")
        self.assertContains(response, "No eligible observations in this period.")

    def test_dashboard_hx_request_returns_only_exact_results_target(self):
        account = create_account("hx-owner")
        create_workout(account, create_template(account))
        self.client.force_login(account.user)

        response = self.client.get(
            reverse("dashboard:index"),
            HTTP_HX_REQUEST="true",
            HTTP_X_FRONTEND_VERSION=frontend_version(),
            HTTP_HX_TARGET="overview-results",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.content.lstrip().startswith(b'<div id="overview-results">'),
            response.content[:120],
        )
        self.assertNotContains(response, "<html")

    def test_dashboard_other_hx_requests_return_the_full_document(self):
        account = create_account("hx-shell-owner")
        self.client.force_login(account.user)

        response = self.client.get(
            reverse("dashboard:index"),
            HTTP_HX_REQUEST="true",
            HTTP_X_FRONTEND_VERSION=frontend_version(),
            HTTP_HX_TARGET="body",
        )

        self.assertContains(response, "<html")

    def test_presenter_localizes_series_and_caps_long_periods(self):
        period = local_period(
            timezone_name="America/Sao_Paulo",
            start=date(2000, 1, 1),
            end=date(2030, 12, 31),
        )
        presentation = DashboardPresenter().present_overview(
            {
                "period": period,
                "metrics": {},
            },
            activity_buckets={date(2020, 1, 1): 2},
        )

        chart = presentation["charts"][0]
        self.assertLessEqual(len(chart["table_rows"]), 60)
        self.assertEqual(chart["table_rows"][0]["label"], "01/01/2026")
        self.assertEqual(chart["view_box"], "0 0 1000 240")
        self.assertLessEqual(len(chart["axis_ticks"]), 5)
        self.assertEqual(
            len({tick["label"] for tick in chart["axis_ticks"]}),
            len(chart["axis_ticks"]),
        )
        self.assertEqual(len(chart["bars"]), len(chart["table_rows"]))


class FractionalChartTests(TestCase):
    def test_fractional_axis_uses_the_same_scale_as_bars(self):
        chart = DashboardPresenter()._categorical_chart(
            dom_id="fraction",
            title="RPE",
            values={"A": 8.5},
            first_header="Session",
            unit="RPE",
        )
        self.assertEqual(chart["axis_ticks"][-1]["label"], "10")
        self.assertAlmostEqual(chart["bars"][0]["y"], 224 - 208 * 0.85)
        count_chart = DashboardPresenter()._categorical_chart(
            dom_id="count",
            title="Sets",
            values={"A": 10},
            first_header="Type",
            unit="sets",
        )
        self.assertEqual(
            [tick["label"] for tick in count_chart["axis_ticks"]], ["0", "5", "10"]
        )
        self.assertLessEqual(count_chart["bars"][0]["width"], 72)
        categories = DashboardPresenter()._categorical_chart(
            dom_id="rpe",
            title="RPE",
            values={7: 1, 7.5: 2, 8: 1, 9: 2, 10: 1},
            first_header="RPE",
            unit="sets",
        )
        self.assertEqual(categories["x_labels"], ["7", "7.5", "8", "9", "10"])
        self.assertEqual(categories["bars"][0]["unit"], "set")
        self.assertEqual(categories["initial_readout"], "10: 1 set")


class ChartWindowTests(TestCase):
    def test_window_navigation_keeps_all_observations_and_handles_bad_pages(self):
        data = {str(i): i for i in range(125)}

        def chart(page):
            return DashboardPresenter(
                query={"chart_page_test": page}
            )._categorical_chart(
                dom_id="test",
                title="Test",
                values=data,
                first_header="Date",
                unit="kg",
                kind="line",
            )

        latest, middle, first = chart(1), chart(2), chart(3)
        self.assertEqual(
            [row["label"] for row in latest["table_rows"]],
            [str(i) for i in range(65, 125)],
        )
        self.assertEqual(
            [row["label"] for row in middle["table_rows"]],
            [str(i) for i in range(5, 65)],
        )
        self.assertEqual(len(first["table_rows"]), 5)
        self.assertEqual(chart("invalid")["page"], 1)
        self.assertEqual(chart(-1)["page"], 1)
        self.assertEqual(chart(999)["page"], 3)
        self.assertEqual(chart(None)["page"], 1)

    def test_missing_observations_break_lines_and_target_controls_axis(self):
        chart = DashboardPresenter()._categorical_chart(
            dom_id="missing",
            title="Missing",
            values={"A": 2, "B": None, "C": 0},
            first_header="Date",
            unit="sets",
            kind="line",
            target=4,
        )
        self.assertEqual(len(chart["segments"]), 2)
        self.assertEqual(chart["table_rows"][1]["value"], "—")
        self.assertEqual(chart["table_rows"][2]["value"], "0")
        self.assertEqual(chart["axis_ticks"][-1]["label"], "4")
        self.assertEqual(chart["target"]["y"], 16)

    def test_navigation_maps_namespaces_and_details(self):
        from types import SimpleNamespace

        from django.contrib.auth.models import AnonymousUser
        from django.urls import resolve

        from accounts.context_processors import application_state

        routes = {
            "/dashboard/": "overview",
            "/dashboard/reports/": "analysis",
            "/history/": "history",
            "/history/1/": "history",
            "/routines/": "routines",
            "/routines/1/": "routines",
            "/exercises/": "exercises",
            "/exercises/1/": "exercises",
            "/planning/": "prompt",
            "/planning/generations/": "prompt",
            "/planning/routines/import/": "routines",
            "/accounts/settings/": "",
        }
        for path, expected in routes.items():
            with self.subTest(path=path):
                context = application_state(
                    SimpleNamespace(user=AnonymousUser(), resolver_match=resolve(path))
                )
                self.assertEqual(context["active_section"], expected)


class SavedReportNavigationTests(TestCase):
    def test_window_links_retain_saved_filters_when_initial_url_is_empty(self):
        from dashboard.models import DashboardPreference

        account = create_account()
        create_workout(account, create_template(account))
        DashboardPreference.objects.create(
            user=account.user,
            panels=["frequency"],
            filters={
                "start": "2020-01-01",
                "end": "2026-08-31",
                "compare": "on",
            },
        )
        self.client.force_login(account.user)
        response = self.client.get(reverse("dashboard:reports"))
        self.assertContains(response, "chart_page_frequency-weeks=2")
        self.assertContains(response, "start=2020-01-01")
        self.assertContains(response, "end=2026-08-31")
        self.assertContains(response, "compare=on")
