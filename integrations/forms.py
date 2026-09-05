
from django import forms
from django.utils.translation import gettext_lazy as _

INPUT_CLASS = (
    'mt-1 w-full rounded-xl border border-forest/20 bg-transparent px-3 py-2 '
    'dark:border-cream/20'
)


class HevyConnectionForm(forms.Form):
    api_key = forms.CharField(
        label=_('Hevy API key'),
        max_length=256,
        strip=True,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'off',
            'spellcheck': 'false',
            'class': INPUT_CLASS,
            'placeholder': _('Paste your key to save the connection'),
        }),
    )


class FullRefreshConfirmationForm(forms.Form):
    confirmation = forms.BooleanField(
        label=_('I confirm the complete synchronization'),
        required=True,
    )
