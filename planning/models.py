import uuid

from django.conf import settings
from django.db import models


class TrainingProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    objective = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    equipment = models.TextField(blank=True)
    available_days = models.CharField(max_length=255, blank=True)
    session_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    limitations = models.TextField(blank=True)


class PromptGeneration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    template_version = models.CharField(max_length=32)
    inputs = models.JSONField()
    manifest = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError(
                "Prompt generations are immutable; create another generation."
            )
        return super().save(*args, **kwargs)


class RoutineProposal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey("integrations.HevyAccount", on_delete=models.CASCADE)
    payload = models.JSONField()
    source_versions = models.JSONField(default=dict)
    changes = models.JSONField(default=list)
    state = models.CharField(max_length=24, default="previewed")
    results = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    submitted_at = models.DateTimeField(null=True)
    local_refresh_pending = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        immutable = {
            "account_id",
            "payload",
            "source_versions",
            "changes",
            "expires_at",
        }
        fields = kwargs.get("update_fields")
        if not self._state.adding and (
            fields is None or immutable.intersection(fields)
        ):
            original = type(self).objects.filter(pk=self.pk).values(*immutable).get()
            if any(getattr(self, name) != original[name] for name in immutable):
                raise ValueError(
                    "Proposal content is immutable; create another preview."
                )
        return super().save(*args, **kwargs)
