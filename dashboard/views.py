from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_headers
from django.views.generic import TemplateView

from analytics.preparation import HistoryPreparationService
from analytics.services import AnalyticsService
from dashboard.forms import PeriodForm
from dashboard.presenters import DashboardPresenter
from integrations.models import IntegrationState
from training.models import ExerciseTemplate


def _account(user):
    return getattr(user, 'hevy_account', None)


@method_decorator(vary_on_headers('HX-Request', 'HX-Target'), name='dispatch')
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_template_names(self):
        if (
            self.request.headers.get('HX-Request') == 'true'
            and self.request.headers.get('HX-Target') == 'overview-results'
        ):
            return ['dashboard/_overview_results.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = _account(self.request.user)
        context['period_form'] = PeriodForm(self.request.GET or None, account=account)
        context['account'] = account
        context['overview'] = None
        context['presentation'] = None
        context['freshness'] = None
        context['comparison'] = None
        if account is None:
            return context
        form = context['period_form']
        compare = False
        if form.is_valid():
            start = form.cleaned_data.get('inicio')
            end = form.cleaned_data.get('fim')
            compare = form.cleaned_data.get('comparar')
            exercise_id = form.cleaned_data.get('exercicio')
        else:
            start = end = None
            exercise_id = None
        service = AnalyticsService(account)
        context['overview'] = service.build_overview(start, end)
        exercise = ExerciseTemplate.objects.filter(
            hevy_account=account, pk=exercise_id
        ).first() if exercise_id else None
        prepared = HistoryPreparationService(
            account, context['overview']['period'], exercise=exercise
        ).build()
        context['presentation'] = DashboardPresenter().present_overview(
            context['overview'], prepared=prepared
        )
        if compare:
            current = context['overview']['period']
            previous_end = current.start - timedelta(days=1)
            previous = service.period(previous_end - timedelta(days=current.days - 1), previous_end)
            context['comparison'] = service.compare_periods(
                lambda selected: service.workout_activity(selected)['workouts'], current, previous
            )
        context['freshness'] = IntegrationState.objects.filter(hevy_account=account).first()
        context['period'] = context['overview']['period']
        return context
