from django.urls import path

from integrations.automatic import AutomaticSyncView
from integrations.views import (
    DisconnectView,
    FullRefreshView,
    IncrementalSyncView,
    LocalExportView,
    PlanRefreshView,
    RetrySyncView,
    SyncRunDetailView,
    SyncView,
    ValidateConnectionView,
)
from planning.views import GenerateView, ImportView

app_name = 'integrations'

urlpatterns = [
    path('sync/auto/', AutomaticSyncView.as_view(), name='automatic'),
    path('sync/', SyncView.as_view(), name='sync'),
    path('sync/connect/', ValidateConnectionView.as_view(), name='validate'),
    path('sync/disconnect/', DisconnectView.as_view(), name='disconnect'),
    path('sync/incremental/', IncrementalSyncView.as_view(), name='incremental'),
    path('sync/full/', FullRefreshView.as_view(), name='full-refresh'),
    path('sync/plans/', PlanRefreshView.as_view(), name='plan-refresh'),
    path('exports/<str:kind>.<str:extension>', LocalExportView.as_view(), name='local-export'),
    path('tools/prompt/', GenerateView.as_view(), name='prompt-template'),
    path('tools/routines/import/', ImportView.as_view(), name='routine-create'),
    path('sync/<uuid:pk>/retry/', RetrySyncView.as_view(), name='retry'),
    path('sync/<uuid:pk>/', SyncRunDetailView.as_view(), name='run-detail'),
]
