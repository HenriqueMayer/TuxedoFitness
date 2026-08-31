from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django import template

register = template.Library()

POUNDS_PER_KILOGRAM = Decimal('2.2046226218')
METERS_PER_MILE = Decimal('1609.344')


def _decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _format(value):
    rounded = value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return format(rounded, 'f').rstrip('0').rstrip('.').replace('.', ',')


@register.filter
def display_mass(value, unit='kg'):
    number = _decimal(value)
    if number is None:
        return '—'
    if unit == 'lb':
        return f'{_format(number * POUNDS_PER_KILOGRAM)} lb'
    return f'{_format(number)} kg'


@register.filter
def display_volume(value, unit='kg'):
    number = _decimal(value)
    if number is None:
        return '—'
    if unit == 'lb':
        return f'{_format(number * POUNDS_PER_KILOGRAM)} lb·rep'
    return f'{_format(number)} kg·rep'


@register.filter
def display_distance(value, unit='km'):
    number = _decimal(value)
    if number is None:
        return '—'
    if unit == 'mi':
        return f'{_format(number / METERS_PER_MILE)} mi'
    return f'{_format(number / Decimal("1000"))} km'
