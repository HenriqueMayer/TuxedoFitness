"""Presentation conversions; stored/provider quantities remain canonical."""

from decimal import Decimal
from zoneinfo import ZoneInfo

from django.utils import timezone

from accounts.templatetags.fitness_units import METERS_PER_MILE, POUNDS_PER_KILOGRAM


def convert_series(values, unit, preference=None):
    if unit in {"kg", "kg·rep"} and getattr(preference, "mass_unit", "kg") == "lb":
        return {
            key: Decimal(value) * POUNDS_PER_KILOGRAM for key, value in values.items()
        }, unit.replace("kg", "lb")
    if unit == "m":
        miles = getattr(preference, "distance_unit", "km") == "mi"
        divisor = METERS_PER_MILE if miles else Decimal(1000)
        return {
            key: Decimal(value) / divisor for key, value in values.items()
        }, "mi" if miles else "km"
    return values, unit


def date_label(value, preference=None, include_time=False):
    if value is None:
        return "—"
    if hasattr(value, "hour"):
        value = timezone.localtime(
            value,
            ZoneInfo(getattr(preference, "presentation_timezone", "America/Sao_Paulo")),
        )
    pattern = (
        "%m/%d/%Y" if getattr(preference, "date_format", "DMY") == "MDY" else "%d/%m/%Y"
    )
    return value.strftime(pattern + (" %H:%M" if include_time else ""))
