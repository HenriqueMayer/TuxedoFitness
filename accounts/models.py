from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class OwnerPreference(models.Model):
    MASS_UNIT_CHOICES = [('kg', 'Quilogramas'), ('lb', 'Libras')]
    DISTANCE_UNIT_CHOICES = [('km', 'Quilômetros'), ('mi', 'Milhas')]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fitness_preferences',
    )
    presentation_timezone = models.CharField(
        max_length=64,
        default='America/Sao_Paulo',
    )
    weekly_session_target = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
    )
    mass_unit = models.CharField(
        max_length=2,
        choices=MASS_UNIT_CHOICES,
        default='kg',
    )
    distance_unit = models.CharField(
        max_length=2,
        choices=DISTANCE_UNIT_CHOICES,
        default='km',
    )
    snapshot_retention_days = models.PositiveSmallIntegerField(
        default=7,
        validators=[MinValueValidator(0), MaxValueValidator(30)],
    )

    def __str__(self):
        return f'Preferências de {self.user.username}'
