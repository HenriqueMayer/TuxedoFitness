from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import CreateView, TemplateView

from accounts.forms import LoginForm, OwnerPreferenceForm, SignupForm
from accounts.models import OwnerPreference
from accounts.services import BackupError, create_verified_backup
from integrations.models import HevyAccount
from training.models import ExerciseTemplate, Routine, Workout


class LoginView(DjangoLoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True


class LogoutView(DjangoLogoutView):
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class SignupView(CreateView):
    form_class = SignupForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('dashboard:index')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        if not settings.ALLOW_SIGNUPS:
            self.object = None
            return self.render_to_response(
                self.get_context_data(signup_disabled=True),
                status=403,
            )
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        OwnerPreference.objects.create(user=self.object)
        login(self.request, self.object)
        messages.success(self.request, _('Your local account was created.'))
        return response


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        preference, created = self._preference()
        context.update({
            'preferences': preference,
            'form': OwnerPreferenceForm(instance=preference),
        })
        return context

    def post(self, request, *args, **kwargs):
        preference, created = self._preference()
        if request.POST.get('action') == 'delete_data':
            return self._delete_data(request)
        form = OwnerPreferenceForm(request.POST, instance=preference)
        if form.is_valid():
            form.save()
            messages.success(request, _('Preferences saved locally.'))
            return redirect('accounts:settings')
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)

    def _preference(self):
        return OwnerPreference.objects.get_or_create(user=self.request.user)

    def _delete_data(self, request):
        if request.POST.get('confirmation', '').strip().upper() not in {'DELETE', 'EXCLUIR'}:
            messages.error(request, _('Type DELETE to confirm local removal.'))
            return redirect('accounts:settings')
        try:
            backup = create_verified_backup()
        except BackupError as error:
            messages.error(request, f'{error.code}: {error}')
            return redirect('accounts:settings')
        account = HevyAccount.objects.filter(user=request.user).first()
        with transaction.atomic():
            if account is not None:
                Workout.all_objects.filter(hevy_account=account).delete()
                Routine.all_objects.filter(hevy_account=account).delete()
                ExerciseTemplate.all_objects.filter(hevy_account=account).delete()
                account.delete()
        messages.success(request, _('Local data removed after verified backup (%(filename)s).') % {'filename': backup.name})
        return redirect('accounts:settings')
