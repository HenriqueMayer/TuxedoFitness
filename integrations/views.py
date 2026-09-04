from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import DatabaseError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView

from integrations.credentials import session_credentials
from integrations.exports import (
    exercise_catalog_csv,
    exercise_catalog_json,
    routines_csv,
    routines_json,
)
from integrations.forms import (
    FullRefreshConfirmationForm,
    HevyConnectionForm,
    PromptTemplateForm,
    RoutineConfirmationForm,
    RoutineJsonForm,
)
from integrations.hevy import HevyClient, HevyError
from integrations.models import (
    IntegrationState,
    RoutineWriteIntent,
    SyncCursor,
    SyncRun,
)
from integrations.prompting import PromptTemplateService
from integrations.routines import (
    RoutinePayloadValidator,
    RoutineValidationError,
    RoutineWriteService,
)
from integrations.services import (
    ADAPTER_VERSION,
    FullImportService,
    IncrementalSyncService,
    PlanRefreshService,
)
from training.models import Routine, Workout


def _account(user):
    return getattr(user, 'hevy_account', None)


def _client_for_request(request):
    api_key = session_credentials.get(request)
    if api_key is None:
        raise HevyError(
            'CONFIG_MISSING_KEY',
            'Conecte sua API key do Hevy novamente para esta sessão.',
        )
    return HevyClient(api_key)


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
            'hevy_documentation_date': '2026-09-04',
            'connection_form': HevyConnectionForm(),
            'session_connected': session_credentials.get(self.request) is not None,
            'history_ready': bool(account and (
                (state and state.last_full_refresh_at)
                or Workout.all_objects.filter(hevy_account=account).exists()
            )),
        })
        return context


class ValidateConnectionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = HevyConnectionForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Informe uma API key válida do Hevy.')
            return redirect('integrations:sync')
        client = HevyClient(form.cleaned_data['api_key'])
        try:
            FullImportService(client).validate_account(request.user)
            session_credentials.put(request, form.cleaned_data['api_key'])
            messages.success(
                request,
                'Conexão validada. A chave ficará somente nesta sessão.',
            )
        except (DatabaseError, HevyError, ValueError) as error:
            _failure_message(request, error)
        return redirect('integrations:sync')


class DisconnectView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        session_credentials.delete(request)
        account = _account(request.user)
        if account is not None:
            IntegrationState.objects.filter(hevy_account=account).update(
                status=IntegrationState.Status.DISCONNECTED,
                is_stale=True,
            )
        messages.success(request, 'A chave do Hevy foi removida desta sessão.')
        return redirect('integrations:sync')


class IncrementalSyncView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        account = _account(request.user)
        if account is None:
            messages.error(request, 'Valide a conexão com o Hevy antes de sincronizar treinos.')
            return redirect('integrations:sync')
        try:
            run = IncrementalSyncService(
                _client_for_request(request)
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
                _client_for_request(request)
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
                _client_for_request(request)
            ).run(
                request.user,
                prior_run=prior_run,
                trigger=SyncRun.Trigger.RETRY,
            )
        except (DatabaseError, HevyError, ValueError) as error:
            _failure_message(request, error)
            return redirect('integrations:run-detail', pk=prior_run.pk)
        return redirect('integrations:run-detail', pk=run.pk)


class PlanRefreshView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            run = PlanRefreshService(_client_for_request(request)).run(
                request.user, trigger=SyncRun.Trigger.WEB
            )
        except (DatabaseError, HevyError, ValueError) as error:
            _failure_message(request, error)
            return redirect('integrations:sync')
        messages.success(request, 'Catálogo e rotinas foram atualizados.')
        return redirect('integrations:run-detail', pk=run.pk)


class LocalExportView(LoginRequiredMixin, View):
    exporters = {
        ('exercises', 'csv'): exercise_catalog_csv,
        ('exercises', 'json'): exercise_catalog_json,
        ('routines', 'csv'): routines_csv,
        ('routines', 'json'): routines_json,
    }

    def get(self, request, kind, extension, *args, **kwargs):
        account = _account(request.user)
        exporter = self.exporters.get((kind, extension))
        if account is None or exporter is None:
            raise Http404
        return exporter(account)


class PromptTemplateView(LoginRequiredMixin, TemplateView):
    template_name = 'integrations/prompt_template.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('form', PromptTemplateForm())
        context.setdefault('generated_prompt', None)
        return context

    def post(self, request, *args, **kwargs):
        account = _account(request.user)
        if account is None:
            messages.error(request, 'Colete o histórico antes de gerar um prompt.')
            return redirect('integrations:sync')
        form = PromptTemplateForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        generated = PromptTemplateService(account).build(form.cleaned_data)
        if request.POST.get('action') == 'download':
            response = HttpResponse(generated, content_type='text/markdown; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="training-analysis-prompt.md"'
            return response
        return self.render_to_response(
            self.get_context_data(form=form, generated_prompt=generated)
        )


class RoutineCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'integrations/routine_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('form', RoutineJsonForm())
        return context

    def post(self, request, *args, **kwargs):
        account = _account(request.user)
        if account is None:
            messages.error(request, 'Atualize o catálogo antes de criar uma rotina.')
            return redirect('integrations:sync')
        form = RoutineJsonForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        validator = RoutinePayloadValidator(account)
        try:
            payload = validator.validate(form.cleaned_data['payload'])
        except RoutineValidationError as error:
            form.add_error('payload', str(error))
            return self.render_to_response(self.get_context_data(form=form))
        intent = RoutineWriteService().create_intent(account, payload)
        return render(request, 'integrations/routine_preview.html', {
            'intent': intent,
            'preview': validator.preview(payload),
            'form': RoutineConfirmationForm(initial={'intent_id': intent.pk}),
        })


class RoutineConfirmView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = RoutineConfirmationForm(request.POST)
        account = _account(request.user)
        if not form.is_valid() or account is None:
            messages.error(request, 'A confirmação da rotina é inválida.')
            return redirect('integrations:routine-create')
        client = None
        try:
            client = _client_for_request(request)
            routine = RoutineWriteService().submit(
                account, form.cleaned_data['intent_id'], client
            )
        except RoutineWriteIntent.DoesNotExist:
            messages.error(request, 'A prévia não existe para esta conta.')
            return redirect('integrations:routine-create')
        except (HevyError, RoutineValidationError) as error:
            _failure_message(request, error)
            return redirect('integrations:routine-create')

        try:
            PlanRefreshService(client).run(request.user, trigger=SyncRun.Trigger.WEB)
        except (DatabaseError, HevyError, ValueError):
            messages.warning(
                request,
                'A rotina foi criada no Hevy, mas os planos locais não puderam ser atualizados. Atualize catálogo e rotinas antes de tentar novamente.',
            )
            return redirect('integrations:sync')
        local_routine = Routine.objects.filter(
            hevy_account=account, external_id=routine.external_id
        ).first()
        messages.success(request, 'Rotina criada no Hevy e confirmada localmente.')
        if local_routine is not None:
            return redirect('training:routine-detail', pk=local_routine.pk)
        return redirect('integrations:sync')
