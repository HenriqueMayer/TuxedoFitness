from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import DatabaseError
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView

from integrations.forms import FullRefreshConfirmationForm
from integrations.hevy import HevyClient, HevyError
from integrations.models import IntegrationState, SyncCursor, SyncRun
from integrations.services import (
    ADAPTER_VERSION,
    FullImportService,
    IncrementalSyncService,
)


def _account(user):
    return getattr(user, 'hevy_account', None)


def _failure_message(request, error):
    if isinstance(error, DatabaseError):
        messages.error(request, 'DATABASE_ERROR: Falha ao persistir os dados locais.')
        return
    code = error.code if isinstance(error, HevyError) else 'SYNC_INVALID'
    messages.error(request, f'{code}: {error}')


class SyncView(LoginRequiredMixin, TemplateView):
    template_name = 'integrations/sync.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = _account(self.request.user)
        state = None
        cursor = None
        runs = SyncRun.objects.none()
        active_run = None
        if account is not None:
            state = IntegrationState.objects.filter(hevy_account=account).first()
            cursor = SyncCursor.objects.filter(
                hevy_account=account, stream_name='workout-events'
            ).first()
            ordered_runs = account.sync_runs.order_by('-created_at')
            runs = ordered_runs[:20]
            active_run = ordered_runs.filter(
                state__in=[SyncRun.State.PENDING, SyncRun.State.RUNNING]
            ).first()
        context.update({
            'account': account,
            'integration_state': state,
            'cursor': cursor,
            'sync_runs': runs,
            'last_run': runs[0] if runs else None,
            'active_run': active_run,
            'adapter_version': ADAPTER_VERSION,
            'hevy_documentation_date': '2026-08-30',
        })
        return context


class ValidateConnectionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            FullImportService(HevyClient.from_environment()).validate_account(request.user)
            messages.success(request, 'Conexão com o Hevy validada. Os dados locais não foram alterados.')
        except (DatabaseError, HevyError, ValueError) as error:
            _failure_message(request, error)
        return redirect('integrations:sync')


class IncrementalSyncView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        account = _account(request.user)
        if account is None:
            messages.error(request, 'Valide a conexão com o Hevy antes de sincronizar treinos.')
            return redirect('integrations:sync')
        try:
            run = IncrementalSyncService(
                HevyClient.from_environment()
            ).run(request.user, trigger=SyncRun.Trigger.WEB)
        except (DatabaseError, HevyError, ValueError) as error:
            _failure_message(request, error)
            failed = SyncRun.objects.filter(
                hevy_account=account,
                state__in=[SyncRun.State.FAILED, SyncRun.State.PARTIAL],
            ).order_by('-created_at').first()
            if failed is not None:
                return redirect('integrations:run-detail', pk=failed.pk)
            return redirect('integrations:sync')
        return redirect('integrations:run-detail', pk=run.pk)


class FullRefreshView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, 'integrations/full_refresh_confirm.html', {
            'form': FullRefreshConfirmationForm(),
        })

    def post(self, request, *args, **kwargs):
        form = FullRefreshConfirmationForm(request.POST)
        if not form.is_valid():
            return render(request, 'integrations/full_refresh_confirm.html', {'form': form})
        try:
            run = FullImportService(
                HevyClient.from_environment()
            ).run(request.user, trigger=SyncRun.Trigger.WEB)
        except (DatabaseError, HevyError, ValueError) as error:
            _failure_message(request, error)
            account = _account(request.user)
            failed = SyncRun.objects.filter(
                hevy_account=account,
                state__in=[SyncRun.State.FAILED, SyncRun.State.PARTIAL],
            ).order_by('-created_at').first() if account is not None else None
            if failed is not None:
                return redirect('integrations:run-detail', pk=failed.pk)
            return redirect('integrations:sync')
        return redirect('integrations:run-detail', pk=run.pk)


class SyncRunDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'integrations/run_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = _account(self.request.user)
        if account is None:
            return context
        context['run'] = get_object_or_404(
            SyncRun, hevy_account=account, pk=self.kwargs['pk']
        )
        return context


class RetrySyncView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        account = _account(request.user)
        if account is None:
            return redirect('integrations:sync')
        prior_run = get_object_or_404(
            SyncRun, hevy_account=account, pk=self.kwargs['pk']
        )
        if (
            prior_run.mode != SyncRun.Mode.INCREMENTAL
            or prior_run.state not in {SyncRun.State.FAILED, SyncRun.State.PARTIAL}
        ):
            messages.error(request, 'Somente execuções incrementais com falha ou parciais podem ser repetidas.')
            return redirect('integrations:run-detail', pk=prior_run.pk)
        try:
            run = IncrementalSyncService(
                HevyClient.from_environment()
            ).run(
                request.user,
                prior_run=prior_run,
                trigger=SyncRun.Trigger.RETRY,
            )
        except (DatabaseError, HevyError, ValueError) as error:
            _failure_message(request, error)
            return redirect('integrations:run-detail', pk=prior_run.pk)
        return redirect('integrations:run-detail', pk=run.pk)
