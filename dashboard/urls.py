from django.urls import path

from dashboard.views import DashboardView, ReportsView

app_name = 'dashboard'

urlpatterns = [path('reports/', ReportsView.as_view(), name='reports'), path('', DashboardView.as_view(), name='index')]
