from django import forms
from django.utils.translation import gettext_lazy as _

from planning.models import TrainingProfile


class StyledForm:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(
                field.widget,
                (forms.CheckboxInput, forms.CheckboxSelectMultiple, forms.HiddenInput),
            ):
                field.widget.attrs["class"] = "input"


class TrainingProfileForm(StyledForm, forms.ModelForm):
    class Meta:
        model = TrainingProfile
        fields = [
            "objective",
            "experience",
            "equipment",
            "available_days",
            "session_minutes",
            "limitations",
        ]
        labels = {
            "objective": _("Objective"),
            "experience": _("Training experience"),
            "equipment": _("Available equipment"),
            "available_days": _("Available days"),
            "session_minutes": _("Minutes per session"),
            "limitations": _("Limitations"),
        }
        widgets = {
            name: forms.Textarea(attrs={"rows": 2, "maxlength": 2000})
            for name in ["objective", "experience", "equipment", "limitations"]
        }

    def clean(self):
        data = super().clean()
        for name in ("objective", "experience", "equipment", "limitations"):
            if len(data.get(name, "")) > 2000:
                self.add_error(name, _("Use at most 2000 characters."))
        return data

    def clean_session_minutes(self):
        value = self.cleaned_data.get("session_minutes")
        if value is not None and not 5 <= value <= 300:
            raise forms.ValidationError(_("Choose between 5 and 300 minutes."))
        return value


class PromptForm(TrainingProfileForm):
    def __init__(self, *args, **kwargs):
        data = args[0] if args else kwargs.get("data")
        if data is not None:
            data = data.copy()
            if data.get("period_mode") != "workouts":
                data["count"] = ""
            if data.get("period_mode") != "custom":
                data["start"] = data["end"] = ""
            if args:
                args = (data, *args[1:])
            else:
                kwargs["data"] = data
        super().__init__(*args, **kwargs)

    comments = forms.CharField(
        label=_("What would you like to change?"),
        required=False,
        max_length=10000,
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "placeholder": _(
                    "Tell us what you enjoy, dislike, or want to improve."
                ),
            }
        ),
    )
    period_mode = forms.ChoiceField(
        label=_("Training history"),
        initial="last_28_days",
        choices=[
            ("last_28_days", _("Last 28 days")),
            ("last_7_days", _("Last 7 days")),
            ("last_month", _("Last month")),
            ("workouts", _("Last N workouts")),
            ("custom", _("Custom dates")),
        ],
    )
    count = forms.IntegerField(
        label=_("Number of workouts"),
        required=False,
        min_value=1,
        max_value=1000,
        initial=10,
    )
    start = forms.DateField(
        label=_("Start date"),
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    end = forms.DateField(
        label=_("End date"),
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def clean(self):
        data = super().clean()
        mode = data.get("period_mode")
        if mode == "workouts" and data.get("count") is None:
            self.add_error("count", _("Enter the number of workouts."))
        if mode != "workouts":
            data["count"] = None
        if mode == "custom":
            if not data.get("start") or not data.get("end"):
                self.add_error("start", _("Choose both dates."))
            elif data["end"] < data["start"]:
                self.add_error(
                    "end", _("The end date must not precede the start date.")
                )
        else:
            data["start"] = data["end"] = None
        return data


class ImportForm(StyledForm, forms.Form):
    payload = forms.CharField(
        label=_("Routine JSON"),
        required=False,
        max_length=2_000_000,
        widget=forms.Textarea(attrs={"rows": 18, "spellcheck": "false"}),
    )
    file = forms.FileField(label=_("Or upload a JSON file"), required=False)

    def clean(self):
        data = super().clean()
        upload = data.get("file")
        if upload and data.get("payload"):
            raise forms.ValidationError(_("Paste JSON or upload a file, not both."))
        if upload:
            if upload.size > 2_000_000:
                raise forms.ValidationError(_("The file exceeds 2 MB."))
            try:
                data["payload"] = upload.read().decode("utf-8-sig")
            except UnicodeError:
                raise forms.ValidationError(_("Use a UTF-8 JSON file.")) from None
        if not data.get("payload"):
            raise forms.ValidationError(_("Provide a JSON document."))
        return data
