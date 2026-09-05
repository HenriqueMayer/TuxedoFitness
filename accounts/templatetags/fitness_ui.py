import json
from decimal import Decimal

from django import template
from django.utils import formats, translation

register = template.Library()


@register.simple_tag(takes_context=True)
def querystring(context, **values):
    query = context['request'].GET.copy()
    for key, value in values.items():
        if value is None:
            query.pop(key, None)
        else:
            query[key] = value
    return query.urlencode()


@register.filter
def pretty_json(value):
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


@register.filter
def exercise_name(value):
    from training.translations import display_name
    return display_name(value)


@register.filter
def metric_value(value):
    if value is None:
        return '—'
    if isinstance(value, dict):
        if 'percent' in value:
            number = value['percent']
            return '—' if number is None else formats.number_format(number, decimal_pos=1) + '%'
        return ' · '.join(f'{key}: {val}' for key, val in value.items() if not isinstance(val, dict))
    if isinstance(value, (float, Decimal)):
        return formats.number_format(value, decimal_pos=2)
    return value


@register.simple_tag(takes_context=True)
def fitness_date(context, value):
    from accounts.presentation import date_label
    return date_label(value, context.get('owner_preferences'))


@register.simple_tag(takes_context=True)
def fitness_datetime(context, value):
    from accounts.presentation import date_label
    return date_label(value, context.get('owner_preferences'), include_time=True)


@register.filter
def translated(value):
    return translation.gettext(str(value))
