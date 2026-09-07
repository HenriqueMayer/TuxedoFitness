"""Localized SVG geometry and bounded observation windows; no metric formulas."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from math import ceil, floor, log10

from django.utils import formats
from django.utils.translation import gettext as _

from accounts.presentation import date_label

MAX_PLOT_POINTS = 60


def _localized_number(value):
    if value is None:
        return "—"
    return formats.number_format(
        Decimal(str(value)).quantize(Decimal("0.01")).normalize(), force_grouping=False
    )


def _axis_scale(maximum):
    """Use readable steps (1, 2, 2.5, 5, 10), keeping zero as the baseline."""
    rough = max(maximum, 1) / 4
    magnitude = 10 ** floor(log10(rough))
    steps = (1, 2, 5, 10) if maximum == int(maximum) else (1, 2, 2.5, 5, 10)
    step = next(n for n in steps if n >= rough / magnitude) * magnitude
    if maximum == int(maximum):
        step = max(1, ceil(step))
    count = ceil(maximum / step)
    limit = count * step
    ticks = [
        {
            "y": round(16 + 208 * (1 - index / count), 2),
            "label": _localized_number(Decimal(str(step)) * index),
        }
        for index in range(count + 1)
    ]
    return limit, ticks


class DashboardPresenter:
    def __init__(self, preference=None, query=None):
        self.preference = preference
        self.query = query or {}

    def label(self, key):
        if isinstance(key, tuple):
            key = key[
                0
            ]  # Session identity remains internal, including duplicate times.
        if isinstance(key, (date, datetime)):
            return date_label(
                key, self.preference, include_time=isinstance(key, datetime)
            )
        if isinstance(key, (int, float, Decimal)):
            return _localized_number(key)
        return str(key)

    def _activity_series(self, period, buckets):
        bucket = "week" if period.days <= 365 else "month"

        def start(day):
            return (
                day.replace(day=1)
                if bucket == "month"
                else day - timedelta(days=day.weekday())
            )

        values = {}
        for day, count in (buckets or {}).items():
            key = start(day)
            values[key] = values.get(key, 0) + (count or 0)
        points, cursor = [], start(period.start)
        while cursor <= start(period.end):
            points.append((cursor, values.get(cursor, 0)))
            cursor = (
                (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
                if bucket == "month"
                else cursor + timedelta(days=7)
            )
        return bucket, points

    def _activity_chart(self, period, buckets):
        bucket, points = self._activity_series(period, buckets)
        chart = self._categorical_chart(
            dom_id="activity-chart",
            title=_("Workouts per week")
            if bucket == "week"
            else _("Workouts per month"),
            values=dict(points),
            partial_keys=[
                day
                for day, _ in points
                if day < period.start
                or (
                    (day.replace(day=28) + timedelta(days=4)).replace(day=1)
                    - timedelta(days=1)
                    if bucket == "month"
                    else day + timedelta(days=6)
                )
                > period.end
            ],
            first_header=_("Period"),
            unit=_("workouts"),
            temporal=True,
            target=getattr(self.preference, "weekly_session_target", None)
            if bucket == "week"
            else None,
        )
        chart["summary"] = _(
            "Sessions by local calendar period. Boundary periods may be incomplete."
        )
        chart["has_data"] = any(count for _, count in points)
        return chart

    def _categorical_chart(
        self,
        *,
        dom_id,
        title,
        values,
        first_header,
        unit,
        kind="bar",
        temporal=False,
        target=None,
        partial_keys=(),
    ):
        items = list(values.items())
        total = len(items)
        pages = max(1, (total + MAX_PLOT_POINTS - 1) // MAX_PLOT_POINTS)
        try:
            page = max(1, min(pages, int(self.query.get("chart_page_" + dom_id, 1))))
        except (ValueError, TypeError):
            page = 1
        end = max(0, total - (page - 1) * MAX_PLOT_POINTS)
        start = max(0, end - MAX_PLOT_POINTS)
        items = items[start:end]
        numeric = [float(value) for _, value in items if value is not None]
        maximum, ticks = _axis_scale(max([1, *numeric, float(target or 0)]))
        horizontal = kind == "horizontal"
        singular_unit = {
            _("sets"): _("set"),
            _("workouts"): _("workout"),
            _("repetitions"): _("repetition"),
        }.get(str(unit), unit)
        # SVG only stretches marks along x. All text is HTML at its native size.
        slot = 1000 / max(len(items), 1)
        bar_width = min(72, slot * 0.55)
        bars, segments, segment = [], [], []
        for index, (key, value) in enumerate(items):
            ratio = 0 if value is None else float(value) / maximum
            x = slot * (index + 0.5)
            y = 224 - ratio * 208
            label = self.label(key)
            if key in partial_keys:
                label += " · " + _("Partial")
            date_key = key[0] if isinstance(key, tuple) else key
            short = (
                date_label(date_key, self.preference)
                if isinstance(date_key, (date, datetime))
                else self.label(key)
            )
            if key in partial_keys:
                short += " *"
            bars.append(
                {
                    "x": round(x - bar_width / 2, 2),
                    "cx": round(x, 2),
                    "y": round(y, 2),
                    "width": round(bar_width, 2),
                    "height": round(224 - y, 2),
                    "rank_width": round(ratio * 1000, 2),
                    "label": label,
                    "tick_label": short,
                    "value": _localized_number(value),
                    "unit": singular_unit if value == 1 else unit,
                    "missing": value is None,
                    "hit_x": round(x - slot / 2, 2),
                    "hit_width": round(slot, 2),
                }
            )
            if value is None:
                if segment:
                    segments.append(" ".join(segment))
                    segment = []
            else:
                segment.append(f"{x:.2f},{y:.2f}")
        if segment:
            segments.append(" ".join(segment))
        label_indexes = sorted({0, (len(bars) - 1) // 2, len(bars) - 1}) if bars else []
        if not temporal and kind != "line" and len(bars) <= 12:
            label_indexes = list(range(len(bars)))
        latest = next((bar for bar in reversed(bars) if not bar["missing"]), None)
        return {
            "dom_id": dom_id,
            "title": title,
            "kind": kind,
            "unit": unit,
            "summary": _("Recorded observations in the selected period."),
            "has_data": bool(numeric),
            "view_box": "0 0 1000 240",
            "bars": bars,
            "segments": segments,
            "axis_ticks": [] if horizontal else ticks,
            "x_labels": [
                b["tick_label"] if i in label_indexes else ""
                for i, b in enumerate(bars)
            ],
            "dense_labels": len(bars) > 6,
            "table_headers": [first_header, unit],
            "table_rows": [{"label": b["label"], "value": b["value"]} for b in bars],
            "initial_readout": f"{latest['label']}: {latest['value']} {latest['unit']}"
            if latest and not horizontal
            else _("Select a point to inspect its value."),
            "target": {
                "y": round(224 - float(target) / maximum * 208, 2),
                "value": target,
            }
            if target
            else None,
            "page": page,
            "pages": pages,
            "total": total,
            "start": start + 1 if total else 0,
            "end": end,
            "older": page + 1 if page < pages else None,
            "newer": page - 1 if page > 1 else None,
            "temporal": temporal or kind == "line",
            "has_partial": any(key in partial_keys for key, _ in items),
        }

    def present_overview(self, overview, *, activity_buckets=None, prepared=None):
        if activity_buckets is None:
            metric = overview.get("metrics", {}).get("activity_buckets")
            activity_buckets = getattr(metric, "value", metric) or {}
        prepared = prepared or {}
        charts = [self._activity_chart(overview["period"], activity_buckets)]
        for identifier, title, values, unit, kind in [
            (
                "set-types-chart",
                _("Sets by type"),
                prepared.get("set_type_counts", {}),
                _("sets"),
                "horizontal",
            ),
            (
                "rpe-chart",
                _("RPE distribution"),
                prepared.get("rpe_distribution", {}),
                _("sets"),
                "bar",
            ),
        ]:
            charts.append(
                self._categorical_chart(
                    dom_id=identifier,
                    title=title,
                    values=values,
                    first_header=_("Observation"),
                    unit=unit,
                    kind=kind,
                )
            )
        if prepared.get("exercise_evolution_title"):
            charts.append(
                self._categorical_chart(
                    dom_id="exercise-evolution-chart",
                    title=_("Progression")
                    + " · "
                    + prepared["exercise_evolution_title"],
                    values=prepared.get("exercise_evolution", {}),
                    first_header=_("Date"),
                    unit=prepared.get("exercise_evolution_unit", _("value")),
                    kind="line",
                )
            )
        return {"charts": charts, "max_plot_points": MAX_PLOT_POINTS}
