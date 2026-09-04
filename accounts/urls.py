from django.urls import path

from accounts.views import LoginView, LogoutView, SettingsView, SignupView

app_name = 'accounts'

urlpatterns = [
    path('entrar/', LoginView.as_view(), name='login'),
    path('cadastro/', SignupView.as_view(), name='signup'),
    path('sair/', LogoutView.as_view(), name='logout'),
    path('configuracoes/', SettingsView.as_view(), name='settings'),
]
