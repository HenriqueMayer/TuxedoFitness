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
    exercicio = forms.ChoiceField(
        required=False,
        label='Evolução do exercício',
        choices=[('', 'Selecione um exercício')],
        widget=forms.Select(attrs={
            'class': 'mt-1 w-full rounded-xl border border-forest/20 bg-transparent px-3 py-2 dark:border-cream/20',
        }),
    )

    def __init__(self, *args, account=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comparar'].widget.attrs['class'] = 'h-4 w-4 rounded border-forest/30'
        today = timezone.localdate()
        self.fields['inicio'].initial = today - timedelta(days=27)
        self.fields['fim'].initial = today
        if account is not None:
            from training.models import ExerciseTemplate

            self.fields['exercicio'].choices = [('', 'Selecione um exercício'), *[
                (str(pk), title)
                for pk, title in ExerciseTemplate.objects.filter(
                    hevy_account=account
                ).order_by('title').values_list('pk', 'title')
            ]]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('inicio') and cleaned.get('fim') and cleaned['fim'] < cleaned['inicio']:
            raise forms.ValidationError('A data final deve ser igual ou posterior à inicial.')
        return cleaned
