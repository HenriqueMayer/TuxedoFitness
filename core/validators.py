from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_aware_datetime(value):
    if value is not None and timezone.is_naive(value):
        raise ValidationError('Datetime values must include a timezone.')
