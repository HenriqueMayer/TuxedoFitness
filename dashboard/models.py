from django.conf import settings
from django.db import models


class DashboardPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    panels = models.JSONField(default=list)
    filters = models.JSONField(default=dict)
    favorites = models.ManyToManyField('training.ExerciseTemplate', blank=True)
