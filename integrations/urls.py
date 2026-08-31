from django.urls import path

from integrations.views import (
    FullRefreshView,
    IncrementalSyncView,
    RetrySyncView,
    SyncRunDetailView,
    SyncView,
    ValidateConnectionView,
)

app_name = 'integrations'

urlpatterns = [
    path('sincronizacao/', SyncView.as_view(), name='sync'),
    path('sincronizacao/validar/', ValidateConnectionView.as_view(), name='validate'),
    path('sincronizacao/incremental/', IncrementalSyncView.as_view(), name='incremental'),
    path('sincronizacao/completa/', FullRefreshView.as_view(), name='full-refresh'),
    path('sincronizacao/<uuid:pk>/repetir/', RetrySyncView.as_view(), name='retry'),
    path('sincronizacao/<uuid:pk>/', SyncRunDetailView.as_view(), name='run-detail'),
]
