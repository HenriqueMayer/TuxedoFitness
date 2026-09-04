from django.urls import path

from integrations.views import (
    DisconnectView,
    FullRefreshView,
    IncrementalSyncView,
    LocalExportView,
    PlanRefreshView,
    PromptTemplateView,
    RetrySyncView,
    RoutineConfirmView,
    RoutineCreateView,
    SyncRunDetailView,
    SyncView,
    ValidateConnectionView,
)

app_name = 'integrations'

urlpatterns = [
    path('sincronizacao/', SyncView.as_view(), name='sync'),
    path('sincronizacao/validar/', ValidateConnectionView.as_view(), name='validate'),
    path('sincronizacao/desconectar/', DisconnectView.as_view(), name='disconnect'),
    path('sincronizacao/incremental/', IncrementalSyncView.as_view(), name='incremental'),
    path('sincronizacao/completa/', FullRefreshView.as_view(), name='full-refresh'),
    path('sincronizacao/planos/', PlanRefreshView.as_view(), name='plan-refresh'),
    path('exportacoes/<str:kind>.<str:extension>', LocalExportView.as_view(), name='local-export'),
    path('ferramentas/prompt/', PromptTemplateView.as_view(), name='prompt-template'),
    path('ferramentas/rotinas/criar/', RoutineCreateView.as_view(), name='routine-create'),
    path('ferramentas/rotinas/confirmar/', RoutineConfirmView.as_view(), name='routine-confirm'),
    path('sincronizacao/<uuid:pk>/repetir/', RetrySyncView.as_view(), name='retry'),
    path('sincronizacao/<uuid:pk>/', SyncRunDetailView.as_view(), name='run-detail'),
]
