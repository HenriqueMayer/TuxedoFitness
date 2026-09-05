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
    path('history/', HistoryView.as_view(), name='history'),
    path('history/<int:pk>/', WorkoutDetailView.as_view(), name='workout-detail'),
    path('exercises/', ExerciseView.as_view(), name='exercises'),
    path('exercises/<int:pk>/', ExerciseDetailView.as_view(), name='exercise-detail'),
    path('routines/', RoutineView.as_view(), name='routines'),
    path('routines/<int:pk>/', RoutineDetailView.as_view(), name='routine-detail'),
    path('exports/workouts.csv', WorkoutExportView.as_view(), name='workout-export'),
]
