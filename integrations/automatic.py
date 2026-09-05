"""Access-triggered synchronization using a separate authenticated POST."""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import DatabaseError, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View

from integrations.credentials import key_for_user
from integrations.hevy import HevyClient, HevyError
from integrations.models import HevyAccount, IntegrationState, ProviderSnapshot, SyncRun
from integrations.services import (
    FullImportService,
    IncrementalSyncService,
    PlanRefreshService,
)


class AutomaticSyncView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            response = self.synchronize(request)
        except DatabaseError:
            response = JsonResponse({"status": "unavailable"}, status=503)
        if "application/json" not in request.headers.get("Accept", ""):
            from django.shortcuts import redirect

            if response.status_code >= 400:
                messages.error(request, _("Hevy unavailable; showing local data"))
            return redirect("integrations:sync")
        return response

    def synchronize(self, request):
        account = HevyAccount.objects.filter(user=request.user).first()
        if account is None or not account.encrypted_api_key:
            return JsonResponse({"status": "disconnected"})
        manual = request.POST.get("manual") == "1"
        now = timezone.now()
        with transaction.atomic():
            state = IntegrationState.objects.select_for_update().get(
                hevy_account=account
            )
            if (
                state.next_auto_attempt_at
                and state.next_auto_attempt_at > now
                and not manual
            ):
                return JsonResponse({"status": "current"})
            # An atomic reservation prevents duplicate requests from different tabs.
            state.next_auto_attempt_at = now + timedelta(minutes=15)
            state.save(update_fields=["next_auto_attempt_at"])
        try:
            client = HevyClient(key_for_user(request.user))
            if not state.last_full_refresh_at:
                FullImportService(client).run(request.user, trigger=SyncRun.Trigger.WEB)
            else:
                if (
                    manual
                    or not state.last_plans_at
                    or state.last_plans_at <= now - timedelta(minutes=15)
                ):
                    catalog = ProviderSnapshot.objects.filter(
                        hevy_account=account, resource="exercise_templates"
                    ).first()
                    if (
                        catalog
                        and state.last_catalog_at
                        and state.last_catalog_at > now - timedelta(days=1)
                    ):
                        client.cached_catalog_pages = catalog.pages
                    PlanRefreshService(client).run(
                        request.user, trigger=SyncRun.Trigger.WEB
                    )
                if (
                    manual
                    or not state.last_incremental_run_at
                    or state.last_incremental_run_at <= now - timedelta(minutes=15)
                ):
                    IncrementalSyncService(client).run(
                        request.user, trigger=SyncRun.Trigger.WEB
                    )
            return JsonResponse({"status": "updated"})
        except (HevyError, DatabaseError, ValueError):
            return JsonResponse({"status": "unavailable"}, status=503)
