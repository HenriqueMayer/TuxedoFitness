import csv
from dataclasses import dataclass

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Exists, OuterRef, Prefetch, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView

from analytics.services import AnalyticsService
from dashboard.forms import PeriodForm
from training.models import (
    ExerciseTemplate,
    Routine,
    RoutineFolder,
    SetType,
    Workout,
    WorkoutExercise,
)


@dataclass(frozen=True)
class PageWindow:
    object_list: list
    number: int
    has_next_value: bool

    def __iter__(self):
        return iter(self.object_list)

    def __len__(self):
        return len(self.object_list)

    def has_previous(self):
        return self.number > 1

    def has_next(self):
        return self.has_next_value

    def has_other_pages(self):
        return self.has_previous() or self.has_next()

    def previous_page_number(self):
        return self.number - 1

    def next_page_number(self):
        return self.number + 1


def _account(user):
    return getattr(user, 'hevy_account', None)


def _period(form, service):
    if form.is_valid():
        return service.period(form.cleaned_data.get('start'), form.cleaned_data.get('end'))
    return service.period()


def _history_queryset(request, account, *, include_removed=False):
    form = PeriodForm(request.GET or None)
    service = AnalyticsService(account)
    period = _period(form, service)
    manager = Workout.all_objects if include_removed else Workout.objects
    queryset = manager.filter(
        hevy_account=account,
    ).select_related('routine').prefetch_related(
        'exercises__exercise_template', 'exercises__sets'
    )
    if request.GET.get('start') or request.GET.get('end'):
        queryset = queryset.filter(start_time__gte=period.start_at, start_time__lt=period.end_at)
    if request.GET.get('q'):
        queryset = queryset.filter(title__icontains=request.GET['q'])
    routine_id = request.GET.get('routine')
    exercise_id = request.GET.get('exercise')
    set_type = request.GET.get('set_type')
    if routine_id and routine_id.isdigit():
        queryset = queryset.filter(routine_id=int(routine_id))
    valid_exercise_id = int(exercise_id) if exercise_id and exercise_id.isdigit() else None
    if set_type:
        matching_exercises = WorkoutExercise.objects.filter(
            workout_id=OuterRef('pk'),
            sets__set_type=set_type,
        )
        if valid_exercise_id is not None:
            matching_exercises = matching_exercises.filter(
                exercise_template_id=valid_exercise_id
            )
        queryset = queryset.filter(Exists(matching_exercises))
    elif valid_exercise_id is not None:
        queryset = queryset.filter(Exists(
            WorkoutExercise.objects.filter(
                workout_id=OuterRef('pk'),
                exercise_template_id=valid_exercise_id,
            )
        ))
    return form, period, queryset


class TrainingSectionView(LoginRequiredMixin, TemplateView):
    pass


class HistoryView(TrainingSectionView):
    template_name = 'training/history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = _account(self.request.user)
        context.update({'set_types': SetType.choices, 'period_form': PeriodForm(), 'page_obj': None, 'account': account, 'routines': [], 'exercise_templates': []})
        if account is None:
            return context
        form, period, queryset = _history_queryset(
            self.request, account, include_removed=False
        )
        context['routines'] = Routine.objects.filter(hevy_account=account)
        context['exercise_templates'] = ExerciseTemplate.objects.filter(hevy_account=account)
        try:
            page_number = max(1, int(self.request.GET.get('page', 1)))
        except (TypeError, ValueError):
            page_number = 1
        offset = (page_number - 1) * 25
        rows = list(queryset[offset:offset + 26])
        context.update({
            'period_form': form,
            'page_obj': PageWindow(rows[:25], page_number, len(rows) > 25),
            'period': period,
        })
        return context


class ExerciseView(TrainingSectionView):
    template_name = 'training/exercises.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = _account(self.request.user)
        query = self.request.GET.get('q', '').strip()
        templates = ExerciseTemplate.objects.filter(hevy_account=account) if account else ExerciseTemplate.objects.none()
        if query:
            templates = templates.filter(Q(title__icontains=query) | Q(title_pt_br__icontains=query) | Q(external_id__icontains=query))
        for param, field in [('muscle', 'primary_muscle'), ('equipment', 'equipment_category'), ('type', 'exercise_type')]:
            if self.request.GET.get(param):
                templates = templates.filter(**{field: self.request.GET[param]})
        from dashboard.models import DashboardPreference
        preference = DashboardPreference.objects.filter(user=self.request.user).first()
        if self.request.GET.get('favorites') == '1':
            templates = templates.filter(pk__in=preference.favorites.values('pk')) if preference else templates.none()
        context.update({'muscles': ExerciseTemplate.MuscleGroup.choices, 'equipment': ExerciseTemplate.EquipmentCategory.choices, 'types': ExerciseTemplate.ExerciseType.choices})
        paginator = Paginator(templates.order_by('title'), 50)
        context.update({
            'account': account,
            'query': query,
            'page_obj': paginator.get_page(self.request.GET.get('page')),
        })
        return context


class WorkoutDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'training/workout_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = _account(self.request.user)
        if account is None:
            raise Http404
        workout = Workout.all_objects.filter(hevy_account=account, pk=self.kwargs['pk']).select_related('routine').prefetch_related('exercises__exercise_template', 'exercises__sets').first()
        if workout is None:
            raise Http404
        context['workout'] = workout
        return context


class ExerciseDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'training/exercise_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = _account(self.request.user)
        if account is None:
            raise Http404
        template = ExerciseTemplate.objects.filter(hevy_account=account, pk=self.kwargs['pk']).prefetch_related('secondary_muscles').first()
        if template is None:
            raise Http404
        service = AnalyticsService(account)
        period = service.period()
        context.update({'exercise_template': template, 'period': period, 'records': service.records(template, period), 'modality': service.modality_metrics(period, exercise=template).get(template.external_id)})
        return context


class RoutineView(TrainingSectionView):
    template_name = 'training/routines.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = _account(self.request.user)
        context['account'] = account
        context['folders'] = []
        context['unfiled_routines'] = []
        if account is None:
            return context
        routine_queryset = Routine.objects.filter(hevy_account=account).select_related('folder').prefetch_related(
            'exercises__exercise_template', 'exercises__sets'
        )
        context['folders'] = RoutineFolder.objects.filter(
            hevy_account=account
        ).prefetch_related(
            Prefetch('routines', queryset=routine_queryset, to_attr='visible_routines')
        )
        context['unfiled_routines'] = [routine for routine in routine_queryset if routine.folder_id is None]
        return context


class RoutineDetailView(TrainingSectionView):
    template_name = 'training/routine_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = _account(self.request.user)
        if account is None:
            raise Http404
        context['routine'] = get_object_or_404(
            Routine.objects.filter(hevy_account=account, pk=self.kwargs['pk'])
            .select_related('folder')
            .prefetch_related('exercises__exercise_template', 'exercises__sets')
        )
        return context


class WorkoutExportView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        account = _account(request.user)
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = (
            f'attachment; filename="workout-history-{timezone.localdate():%Y%m%d}.csv"'
        )
        writer = csv.writer(response, lineterminator='\n')
        writer.writerow([
            'workout_id', 'workout_title', 'start_time_utc', 'end_time_utc', 'routine',
            'exercise_template_id', 'exercise', 'set_type', 'weight_kg', 'reps',
            'distance_meters', 'duration_seconds', 'rpe', 'custom_metric',
            'status', 'removed_at',
        ])
        if account is None:
            return response
        _, _, queryset = _history_queryset(request, account, include_removed=False)
        exercise_id = request.GET.get('exercise') or ''
        set_type = request.GET.get('set_type')
        for workout in queryset:
            for exercise in workout.exercises.all():
                if exercise_id.isdigit() and exercise.exercise_template_id != int(exercise_id):
                    continue
                for recorded_set in exercise.sets.all():
                    if set_type and recorded_set.set_type != set_type:
                        continue
                    writer.writerow([
                        workout.pk,
                        workout.title,
                        workout.start_time.isoformat(),
                        workout.end_time.isoformat(),
                        workout.routine.title if workout.routine else '',
                        exercise.exercise_template_id,
                        exercise.title_snapshot,
                        recorded_set.set_type,
                        recorded_set.weight_kg if recorded_set.weight_kg is not None else '',
                        recorded_set.reps if recorded_set.reps is not None else '',
                        recorded_set.distance_meters if recorded_set.distance_meters is not None else '',
                        recorded_set.duration_seconds if recorded_set.duration_seconds is not None else '',
                        recorded_set.rpe if recorded_set.rpe is not None else '',
                        recorded_set.custom_metric if recorded_set.custom_metric is not None else '',
                        'removed' if not workout.is_active else 'active',
                        workout.removed_at.isoformat() if workout.removed_at else '',
                    ])
        return response
