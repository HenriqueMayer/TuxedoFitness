from django.urls import path

from training.views import (
    ExerciseDetailView,
    ExerciseView,
    HistoryView,
    RoutineDetailView,
    RoutineView,
    WorkoutDetailView,
    WorkoutExportView,
)

app_name = 'training'

urlpatterns = [
    path('historico/', HistoryView.as_view(), name='history'),
    path('historico/<int:pk>/', WorkoutDetailView.as_view(), name='workout-detail'),
    path('exercicios/', ExerciseView.as_view(), name='exercises'),
    path('exercicios/<int:pk>/', ExerciseDetailView.as_view(), name='exercise-detail'),
    path('rotinas/', RoutineView.as_view(), name='routines'),
    path('rotinas/<int:pk>/', RoutineDetailView.as_view(), name='routine-detail'),
    path('exportacoes/treinos.csv', WorkoutExportView.as_view(), name='workout-export'),
]
