from django.urls import include, path

from core.views import health, readiness

urlpatterns = [
    path('', include('pages.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('conta/', include('accounts.urls')),
    path('', include('training.urls')),
    path('', include('integrations.urls')),
    path('health/', health, name='health'),
    path('ready/', readiness, name='readiness'),
]
