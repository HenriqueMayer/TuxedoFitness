from datetime import timedelta

from django import forms
from django.utils import timezone


class PeriodForm(forms.Form):
    inicio = forms.DateField(
        required=False,
        label='Início',
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'type': 'date',
            'lang': 'pt-BR',
            'class': 'mt-1 w-full rounded-xl border border-forest/20 bg-transparent px-3 py-2 dark:border-cream/20',
        }),
    )
    fim = forms.DateField(
        required=False,
        label='Fim',
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'type': 'date',
            'lang': 'pt-BR',
            'class': 'mt-1 w-full rounded-xl border border-forest/20 bg-transparent px-3 py-2 dark:border-cream/20',
        }),
    )
    comparar = forms.BooleanField(
        required=False,
        label='Comparar com o período anterior',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comparar'].widget.attrs['class'] = 'h-4 w-4 rounded border-forest/30'
        today = timezone.localdate()
        self.fields['inicio'].initial = today - timedelta(days=27)
        self.fields['fim'].initial = today

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('inicio') and cleaned.get('fim') and cleaned['fim'] < cleaned['inicio']:
            raise forms.ValidationError('A data final deve ser igual ou posterior à inicial.')
        return cleaned
