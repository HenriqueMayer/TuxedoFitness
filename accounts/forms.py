from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from accounts.models import OwnerPreference

INPUT_CLASSES = (
    'w-full rounded-xl border border-forest/20 bg-white px-4 py-3 text-forest '
    'focus:border-caramel focus:outline-none focus:ring-2 focus:ring-caramel/40 '
    'dark:border-cream/20 dark:bg-forest-deep dark:text-cream'
)


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASSES


class SignupForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        labels = {
            'username': 'Nome de usuário',
            'email': 'E-mail',
            'password1': 'Senha',
            'password2': 'Confirmação da senha',
        }
        for name, field in self.fields.items():
            field.label = labels.get(name, field.label)
            field.widget.attrs['class'] = INPUT_CLASSES


class OwnerPreferenceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_classes = (
            'mt-1 w-full rounded-xl border border-forest/20 bg-white px-3 py-2 '
            'dark:border-cream/20 dark:bg-forest-deep'
        )
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', input_classes)

    class Meta:
        model = OwnerPreference
        fields = (
            'presentation_timezone',
            'weekly_session_target',
            'mass_unit',
            'distance_unit',
            'snapshot_retention_days',
        )
        labels = {
            'presentation_timezone': 'Fuso horário',
            'weekly_session_target': 'Meta semanal de sessões',
            'mass_unit': 'Unidade de massa',
            'distance_unit': 'Unidade de distância',
            'snapshot_retention_days': 'Retenção de snapshots (dias)',
        }
        help_texts = {
            'mass_unit': 'Afeta apenas a apresentação; o banco e o CSV permanecem em kg.',
            'distance_unit': 'Afeta apenas a apresentação; o banco e o CSV permanecem em metros.',
            'snapshot_retention_days': 'De 0 a 30; aplicado pela manutenção agendada.',
        }
        widgets = {
            'presentation_timezone': forms.TextInput(attrs={'autocomplete': 'off'}),
            'weekly_session_target': forms.NumberInput(attrs={'min': 1}),
            'snapshot_retention_days': forms.NumberInput(attrs={'min': 0, 'max': 30}),
        }

    def clean_presentation_timezone(self):
        value = self.cleaned_data['presentation_timezone'].strip()
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise forms.ValidationError('Informe um fuso horário IANA válido.') from error
        return value
