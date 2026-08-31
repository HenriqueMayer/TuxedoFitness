from django import forms


class FullRefreshConfirmationForm(forms.Form):
    confirmation = forms.BooleanField(
        label='Confirmo a atualização completa',
        required=True,
    )
