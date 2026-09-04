"""Presentation-only helpers for the server-rendered dashboard."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, TypedDict

from analytics.services import LocalPeriod

MAX_PLOT_POINTS = 2_000
SVG_WIDTH = 720
SVG_HEIGHT = 280
SVG_MARGIN = {'top': 20, 'right': 16, 'bottom': 54, 'left': 48}


class BarViewModel(TypedDict):
    x: float
    y: float
    width: float
    height: float
    label: str
    value: Any
    show_label: bool


class AxisTickViewModel(TypedDict):
    y: float
    label: str


class ChartViewModel(TypedDict):
    dom_id: str
    title: str
    aria_label: str
    summary: str
    has_data: bool
    view_box: str
    bars: list[BarViewModel]
    axis_ticks: list[AxisTickViewModel]
    table_headers: list[str]
    table_rows: list[dict[str, str]]
    unit: str


def _period_bucket(period: LocalPeriod) -> str:
    return 'week' if period.days <= 365 else 'month'


def _bucket_start(value: date, bucket: str) -> date:
    if bucket == 'month':
        return value.replace(day=1)
    return value - timedelta(days=value.weekday())


def _localized_date(value: date, *, include_year: bool) -> str:
    return value.strftime('%d/%m/%Y' if include_year else '%d/%m')


def _localized_number(value: Any) -> str:
    if value is None:
        return ''
    return str(value).replace('.', ',')


def _axis_ticks(maximum: int, chart_height: float) -> list[AxisTickViewModel]:
    top = SVG_MARGIN['top']
    baseline = top + chart_height
    if maximum <= 4:
        values = list(range(maximum + 1))
    else:
        values = list(dict.fromkeys(round(maximum * index / 4) for index in range(5)))
    return [
        {
            'y': round(baseline - chart_height * value / maximum, 2),
            'label': str(value),
        }
        for value in values
    ]


class DashboardPresenter:
    """Turn analytics read models into localized SVG and table payloads."""

    def _activity_series(
        self, period: LocalPeriod, buckets: dict[date, int | None] | None
    ) -> tuple[str, list[tuple[date, int | None]]]:
        values = {
            _bucket_start(key, _period_bucket(period)): value
            for key, value in (buckets or {}).items()
        }
        bucket = _period_bucket(period)
        first = _bucket_start(period.start, bucket)
        last = _bucket_start(period.end, bucket)
        points: list[tuple[date, int | None]] = []
        cursor = first
        while cursor <= last:
            points.append((cursor, values.get(cursor, 0)))
            if bucket == 'month':
                cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
            else:
                cursor += timedelta(days=7)

        if len(points) <= MAX_PLOT_POINTS:
            return bucket, points

        monthly: dict[date, int] = {}
        for key, value in points:
            month = key.replace(day=1)
            monthly[month] = monthly.get(month, 0) + (value or 0)
        return 'month', sorted(monthly.items())[:MAX_PLOT_POINTS]

    def _activity_chart(
        self, period: LocalPeriod, buckets: dict[date, int | None]
    ) -> ChartViewModel:
        bucket, points = self._activity_series(period, buckets)
        include_year = period.days > 365
        labels = [_localized_date(key, include_year=include_year) for key, _ in points]
        values = [int(value or 0) for _, value in points]
        total = sum(values)
        has_data = any(value > 0 for value in values)
        bucket_label = 'semana' if bucket == 'week' else 'mês'
        title = f'Treinos por {bucket_label}'
        summary = (
            f'{total} treino(s) registrado(s) no período, agrupado(s) por {bucket_label}.'
            if has_data
            else 'Nenhum treino confirmado no período selecionado.'
        )

        chart_width = SVG_WIDTH - SVG_MARGIN['left'] - SVG_MARGIN['right']
        chart_height = SVG_HEIGHT - SVG_MARGIN['top'] - SVG_MARGIN['bottom']
        slot_width = chart_width / max(len(values), 1)
        bar_width = max(1.0, slot_width * 0.64)
        maximum = max(max(values, default=0), 1)
        label_step = max(1, (len(labels) + 7) // 8)
        bars: list[BarViewModel] = []
        for index, (label, value) in enumerate(zip(labels, values, strict=True)):
            height = chart_height * value / maximum
            bars.append({
                'x': round(SVG_MARGIN['left'] + index * slot_width + (slot_width - bar_width) / 2, 2),
                'y': round(SVG_MARGIN['top'] + chart_height - height, 2),
                'width': round(bar_width, 2),
                'height': round(height, 2),
                'label': label,
                'value': value,
                'show_label': index % label_step == 0 or index == len(labels) - 1,
            })

        return {
            'dom_id': 'activity-chart',
            'title': title,
            'aria_label': f'{title}: {summary}',
            'summary': summary,
            'has_data': has_data,
            'view_box': f'0 0 {SVG_WIDTH} {SVG_HEIGHT}',
            'bars': bars,
            'axis_ticks': _axis_ticks(maximum, chart_height),
            'table_headers': ['Período', 'Treinos'],
            'table_rows': [
                {'label': label, 'value': _localized_number(value)}
                for label, value in zip(labels, values, strict=True)
            ],
            'unit': 'treino(s)',
        }

    def _categorical_chart(
        self, *, dom_id, title, values, first_header, unit,
        summarize_points=False,
    ) -> ChartViewModel:
        labels = list(values)
        numeric = [float(values[label]) for label in labels]
        total = sum(values.values())
        has_data = bool(labels) and any(value > 0 for value in numeric)
        summary = (
            f'{len(labels)} ponto(s) de evolução em {unit}.'
            if has_data and summarize_points else
            f'{_localized_number(total)} {unit} no período selecionado.'
            if has_data else f'Sem dados de {title.lower()} no período selecionado.'
        )
        chart_width = SVG_WIDTH - SVG_MARGIN['left'] - SVG_MARGIN['right']
        chart_height = SVG_HEIGHT - SVG_MARGIN['top'] - SVG_MARGIN['bottom']
        slot_width = chart_width / max(len(numeric), 1)
        bar_width = max(1.0, slot_width * 0.64)
        maximum = max(max(numeric, default=0), 1)
        bars: list[BarViewModel] = []
        for index, (label, value) in enumerate(zip(labels, numeric, strict=True)):
            height = chart_height * value / maximum
            bars.append({
                'x': round(SVG_MARGIN['left'] + index * slot_width + (slot_width - bar_width) / 2, 2),
                'y': round(SVG_MARGIN['top'] + chart_height - height, 2),
                'width': round(bar_width, 2),
                'height': round(height, 2),
                'label': label,
                'value': _localized_number(values[label]),
                'show_label': True,
            })
        return {
            'dom_id': dom_id,
            'title': title,
            'aria_label': f'{title}: {summary}',
            'summary': summary,
            'has_data': has_data,
            'view_box': f'0 0 {SVG_WIDTH} {SVG_HEIGHT}',
            'bars': bars,
            'axis_ticks': _axis_ticks(max(1, int(maximum + 0.999)), chart_height),
            'table_headers': [first_header, unit],
            'table_rows': [
                {'label': label, 'value': _localized_number(values[label])}
                for label in labels
            ],
            'unit': unit,
        }

    def present_overview(
        self, overview: dict[str, Any], *, activity_buckets=None, prepared=None
    ) -> dict[str, Any]:
        """Return presentation metadata without recalculating analytics."""

        period = overview['period']
        if activity_buckets is None:
            metric = overview.get('metrics', {}).get('activity_buckets')
            activity_buckets = getattr(metric, 'value', metric) or {}
        prepared = prepared or {}
        charts = [self._activity_chart(period, activity_buckets)]
        charts.append(self._categorical_chart(
            dom_id='set-types-chart', title='Séries por tipo',
            values=prepared.get('set_type_counts', {}), first_header='Tipo', unit='série(s)',
        ))
        charts.append(self._categorical_chart(
            dom_id='rpe-chart', title='Distribuição de RPE',
            values=prepared.get('rpe_distribution', {}), first_header='RPE', unit='série(s)',
        ))
        if prepared.get('exercise_evolution_title'):
            charts.append(self._categorical_chart(
                dom_id='exercise-evolution-chart',
                title=f"Evolução · {prepared['exercise_evolution_title']}",
                values=prepared.get('exercise_evolution', {}),
                first_header='Data', unit=prepared.get('exercise_evolution_unit', 'valor'),
                summarize_points=True,
            ))
        return {
            'charts': charts,
            'max_plot_points': MAX_PLOT_POINTS,
        }
