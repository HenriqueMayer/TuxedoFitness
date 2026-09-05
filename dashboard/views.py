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
            start = form.cleaned_data.get('start')
            end = form.cleaned_data.get('end')
            compare = form.cleaned_data.get('compare')
            exercise_id = form.cleaned_data.get('exercise')
        else:
            start = end = None
            exercise_id = None
        service = AnalyticsService(account)
        context['overview'] = service.build_overview(start, end)
        from training.models import Workout
        context['recent_workouts'] = Workout.objects.filter(hevy_account=account).order_by('-start_time')[:5]
        exercise = ExerciseTemplate.objects.filter(
            hevy_account=account, pk=exercise_id
        ).first() if exercise_id else None
        prepared = HistoryPreparationService(
            account, context['overview']['period'], exercise=exercise
        ).build()
        context['presentation'] = DashboardPresenter(getattr(self.request.user, 'fitness_preferences', None)).present_overview(
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


class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/reports.html'

    def get_context_data(self, **kwargs):
        from dashboard.models import DashboardPreference
        from dashboard.reports import PANELS, PreferenceForm, ReportForm, build_reports
        context = super().get_context_data(**kwargs)
        account = _account(self.request.user)
        preference = DashboardPreference.objects.filter(user=self.request.user).first()
        selected_panels = preference.panels if preference else [key for key, _ in PANELS]
        panel = self.request.GET.get('panel', selected_panels[0] if selected_panels else 'frequency')
        if panel not in dict(PANELS):
            panel = 'frequency'
        data = self.request.GET if self.request.GET else (preference.filters if preference else {})
        form = ReportForm(data, account=account, panel=panel)
        context.update({'filter_form': form, 'panel': panel,
            'panels': [(key, dict(PANELS)[key]) for key in selected_panels],
            'preferences_form': PreferenceForm(account=account, initial={
                'panels': selected_panels, 'order': selected_panels,
                'favorites': preference.favorites.all() if preference else [],
            })})
        if account and form.is_valid():
            context.update(build_reports(account, form.cleaned_data, panel))
        return context

    def post(self, request, **kwargs):
        from django.shortcuts import redirect

        from dashboard.models import DashboardPreference
        from dashboard.reports import PANELS, PreferenceForm, ReportForm
        preference, _ = DashboardPreference.objects.get_or_create(user=request.user,
            defaults={'panels': [key for key, _ in PANELS]})
        form = PreferenceForm(request.POST, account=_account(request.user))
        if request.POST.get('action') == 'save_filters':
            form = ReportForm(request.POST, account=_account(request.user), panel=request.POST.get("panel", "frequency"))
            if form.is_valid():
                preference.filters = {key: str(getattr(value, 'pk', value)) if value is not None else '' for key, value in form.cleaned_data.items()}
                preference.save(update_fields=['filters'])
                return redirect('dashboard:reports')
        elif form.is_valid():
            selected = form.cleaned_data['panels']
            order = form.cleaned_data['order']
            preference.panels = [key for key in order if key in selected] + [key for key in selected if key not in order]
            preference.save(update_fields=['panels'])
            preference.favorites.set(form.cleaned_data['favorites'])
            return redirect('dashboard:reports')
        context = self.get_context_data()
        context['filter_form' if request.POST.get('action') == 'save_filters' else 'preferences_form'] = form
        return self.render_to_response(context)
