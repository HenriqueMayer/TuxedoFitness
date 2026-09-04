import json

from django import forms
from django.db import models

INPUT_CLASS = (
    'mt-1 w-full rounded-xl border border-forest/20 bg-transparent px-3 py-2 '
    'dark:border-cream/20'
)


class HevyConnectionForm(forms.Form):
    api_key = forms.CharField(
        label='API key do Hevy',
        max_length=256,
        strip=True,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'off',
            'spellcheck': 'false',
            'class': INPUT_CLASS,
            'placeholder': 'Cole sua chave somente para esta sessão',
        }),
    )


class FullRefreshConfirmationForm(forms.Form):
    confirmation = forms.BooleanField(
        label='Confirmo a atualização completa',
        required=True,
    )


class RoutineJsonForm(forms.Form):
    payload = forms.CharField(
        label='JSON da rotina',
        max_length=65_536,
        widget=forms.Textarea(attrs={
            'rows': 18,
            'class': f'{INPUT_CLASS} font-mono text-sm',
            'spellcheck': 'false',
            'placeholder': '{"routine": {"title": "...", "exercises": [...]}}',
        }),
    )

    def clean_payload(self):
        value = self.cleaned_data['payload']
        try:
            payload = json.loads(value)
        except json.JSONDecodeError as error:
            raise forms.ValidationError(
                f'JSON inválido na linha {error.lineno}, coluna {error.colno}.'
            ) from error
        if not isinstance(payload, dict):
            raise forms.ValidationError('O JSON deve ser um objeto.')
        return payload


class RoutineConfirmationForm(forms.Form):
    intent_id = forms.UUIDField(widget=forms.HiddenInput())
    confirmation = forms.BooleanField(
        label='Confirmo a criação desta rotina na minha conta Hevy',
        required=True,
    )


class PromptTemplateForm(forms.Form):
    class PeriodMode(models.TextChoices):
        LAST_SEVEN_DAYS = 'last_7_days', 'Últimos 7 dias'
        WEEKS = 'weeks', 'N semanas'
        WORKOUTS = 'workouts', 'N treinos'
        MONTHS = 'months', 'N meses'

    objective = forms.CharField(label='Objetivo', max_length=500, widget=forms.Textarea(attrs={
        'rows': 3, 'class': INPUT_CLASS,
    }))
    desired_frequency = forms.IntegerField(
        label='Frequência desejada por semana', min_value=1, max_value=14,
        widget=forms.NumberInput(attrs={'class': INPUT_CLASS}),
    )
    session_duration_minutes = forms.IntegerField(
        label='Duração desejada por sessão (minutos)', min_value=5, max_value=300,
        widget=forms.NumberInput(attrs={'class': INPUT_CLASS}),
    )
    available_equipment = forms.CharField(
        label='Equipamentos disponíveis', max_length=2_000,
        widget=forms.Textarea(attrs={'rows': 3, 'class': INPUT_CLASS}),
    )
    limitations = forms.CharField(
        label='Limitações', max_length=2_000, required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': INPUT_CLASS}),
    )
    observations = forms.CharField(
        label='Observações', max_length=2_000, required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': INPUT_CLASS}),
    )
    period_mode = forms.ChoiceField(
        label='Histórico incluído', choices=PeriodMode.choices,
        widget=forms.Select(attrs={'class': INPUT_CLASS}),
    )
    period_value = forms.IntegerField(
        label='Quantidade', min_value=1, required=False,
        widget=forms.NumberInput(attrs={'class': INPUT_CLASS}),
    )

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get('period_mode')
        value = cleaned.get('period_value')
        limits = {
            self.PeriodMode.WEEKS: 52,
            self.PeriodMode.WORKOUTS: 100,
            self.PeriodMode.MONTHS: 24,
        }
        if mode == self.PeriodMode.LAST_SEVEN_DAYS:
            cleaned['period_value'] = 1
        elif mode in limits:
            if value is None:
                self.add_error('period_value', 'Informe a quantidade para o período selecionado.')
            elif value > limits[mode]:
                self.add_error('period_value', f'O limite para esta opção é {limits[mode]}.')
        return cleaned
