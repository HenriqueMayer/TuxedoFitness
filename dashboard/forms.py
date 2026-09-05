from datetime import date, timedelta

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class PeriodForm(forms.Form):
    start = forms.DateField(
        required=False,
        label=_('Start date'),
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'type': 'date',

            'class': 'mt-1 w-full rounded-xl border border-forest/20 bg-transparent px-3 py-2 dark:border-cream/20',
        }),
    )
    end = forms.DateField(
        required=False,
        label=_('End date'),
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'type': 'date',

            'class': 'mt-1 w-full rounded-xl border border-forest/20 bg-transparent px-3 py-2 dark:border-cream/20',
        }),
    )
    compare = forms.BooleanField(
        required=False,
        label=_('Compare with previous period'),
    )
    exercise = forms.ChoiceField(
        required=False,
        label=_('Exercise progression'),
        choices=[('', _('Select an exercise'))],
        widget=forms.Select(attrs={
            'class': 'mt-1 w-full rounded-xl border border-forest/20 bg-transparent px-3 py-2 dark:border-cream/20',
        }),
    )

    def __init__(self, *args, account=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['compare'].widget.attrs['class'] = 'h-4 w-4 rounded border-forest/30'
        from analytics.services import AnalyticsService
        today = AnalyticsService(account).period().end if account else timezone.localdate()
        self.fields['start'].initial = today - timedelta(days=27)
        self.fields['end'].initial = today
        if account is not None:
            from training.models import ExerciseTemplate
            from training.translations import display_name

            self.fields['exercise'].choices = [('', _('Select an exercise')), *[
                (str(template.pk), display_name(template))
                for template in ExerciseTemplate.objects.filter(
                    hevy_account=account
                ).order_by('title')
            ]]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('end') == date.max:
            raise forms.ValidationError(_('Choose an end date before 9999-12-31.'))
        if cleaned.get('start') and cleaned.get('end') and cleaned['end'] < cleaned['start']:
            raise forms.ValidationError(_('The end date must not precede the start date.'))
        return cleaned
