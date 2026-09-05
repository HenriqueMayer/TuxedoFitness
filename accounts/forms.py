from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from accounts.models import OwnerPreference

INPUT_CLASSES = (
    'w-full rounded-xl border border-forest/20 bg-white px-4 py-3 text-forest '
    'focus:border-caramel focus:outline-none focus:ring-2 focus:ring-caramel/40 '
    'dark:border-cream/20 dark:bg-night dark:text-cream'
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
            'username': _('Username'),
            'email': _('Email'),
            'password1': _('Password'),
            'password2': _('Password confirmation'),
        }
        for name, field in self.fields.items():
            field.label = labels.get(name, field.label)
            field.widget.attrs['class'] = INPUT_CLASSES


class OwnerPreferenceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_classes = (
            'mt-1 w-full rounded-xl border border-forest/20 bg-white px-3 py-2 '
            'dark:border-cream/20 dark:bg-night'
        )
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', input_classes)

    class Meta:
        model = OwnerPreference
        fields = (
            'presentation_timezone',
            'date_format',
            'weekly_session_target',
            'mass_unit',
            'distance_unit',
            'snapshot_retention_days',
        )
        labels = {
            'presentation_timezone': _('Timezone'),
            'weekly_session_target': _('Weekly session target'),
            'mass_unit': _('Mass unit'),
            'distance_unit': _('Distance unit'),
            'snapshot_retention_days': _('Diagnostic retention (days)'),
        }
        help_texts = {
            'mass_unit': _('Presentation only; stored values and CSV use kilograms.'),
            'distance_unit': _('Presentation only; stored values and CSV use metres.'),
            'snapshot_retention_days': _('From 0 to 30 days; applied by scheduled maintenance.'),
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
            raise forms.ValidationError(_('Enter a valid IANA timezone.')) from error
        return value
