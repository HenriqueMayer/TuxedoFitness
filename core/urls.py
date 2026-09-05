from django.urls import include, path

from core.views import health, readiness

urlpatterns = [
    path('', include('pages.urls')),
    path('planning/', include('planning.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('dashboard/', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('', include('training.urls')),
    path('', include('integrations.urls')),
    path('health/', health, name='health'),
    path('ready/', readiness, name='readiness'),
]
