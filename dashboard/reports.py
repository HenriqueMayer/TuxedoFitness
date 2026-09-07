"""Configurable local analytics; presentation receives calculated series only."""

from datetime import date

from django import forms
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from accounts.presentation import convert_series, date_label
from analytics.reporting import build_report_data
from dashboard.presenters import DashboardPresenter
from planning.forms import StyledForm
from training.models import ExerciseTemplate, Routine, SetType

PANELS = [
    ("frequency", gettext_lazy("Frequency and consistency")),
    ("progression", gettext_lazy("Load and progression")),
    ("effort", gettext_lazy("Recorded effort")),
    ("volume", gettext_lazy("Training volume")),
    ("distribution", gettext_lazy("Training distribution")),
    ("duration", gettext_lazy("Duration and modalities")),
]


class ReportForm(StyledForm, forms.Form):
    grouping = forms.ChoiceField(
        required=False,
        label=gettext_lazy("Group frequency by"),
        choices=[("week", gettext_lazy("Week")), ("month", gettext_lazy("Month"))],
    )
    start = forms.DateField(
        required=False,
        label=gettext_lazy("Start date"),
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    end = forms.DateField(
        required=False,
        label=gettext_lazy("End date"),
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    exercise = forms.ModelChoiceField(
        queryset=ExerciseTemplate.objects.none(),
        required=False,
        label=gettext_lazy("Exercise"),
    )
    routine = forms.ModelChoiceField(
        queryset=Routine.objects.none(), required=False, label=gettext_lazy("Routine")
    )
    muscle = forms.ChoiceField(
        required=False,
        label=gettext_lazy("Primary muscle"),
        choices=[("", gettext_lazy("All"))]
        + list(ExerciseTemplate.MuscleGroup.choices),
    )
    equipment = forms.ChoiceField(
        required=False,
        label=gettext_lazy("Equipment"),
        choices=[("", gettext_lazy("All"))]
        + list(ExerciseTemplate.EquipmentCategory.choices),
    )
    set_type = forms.ChoiceField(
        required=False,
        label=gettext_lazy("Set type"),
        choices=[("", gettext_lazy("All"))] + list(SetType.choices),
    )
    compare = forms.BooleanField(
        required=False, label=gettext_lazy("Compare with previous period")
    )

    def __init__(self, *args, account=None, panel="frequency", **kwargs):
        super().__init__(*args, **kwargs)
        if panel != "frequency":
            self.fields.pop("grouping")
        self.fields["exercise"].queryset = ExerciseTemplate.objects.filter(
            hevy_account=account
        )
        from training.translations import display_name

        self.fields["exercise"].label_from_instance = display_name
        self.fields["exercise"].empty_label = gettext_lazy("All")
        self.fields["routine"].empty_label = gettext_lazy("All")
        self.fields["routine"].queryset = Routine.objects.filter(hevy_account=account)

    def clean(self):
        values = super().clean()
        if values.get("end") == date.max:
            self.add_error("end", gettext_lazy("Choose an end date before 9999-12-31."))
        if (
            values.get("start")
            and values.get("end")
            and values["end"] < values["start"]
        ):
            self.add_error(
                "end", gettext_lazy("The end date must not precede the start date.")
            )
        return values


class PreferenceForm(StyledForm, forms.Form):
    panels = forms.MultipleChoiceField(
        label=gettext_lazy("Visible panels"),
        choices=PANELS,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    favorites = forms.ModelMultipleChoiceField(
        label=gettext_lazy("Favorite exercises"),
        queryset=ExerciseTemplate.objects.none(),
        required=False,
    )

    def __init__(self, *args, account=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["favorites"].queryset = ExerciseTemplate.objects.filter(
            hevy_account=account
        )
        from training.translations import display_name

        self.fields["favorites"].label_from_instance = display_name
        order = self.initial.get("order", [])
        for index in range(1, len(PANELS) + 1):
            self.fields[f"position_{index}"] = forms.ChoiceField(
                label=gettext_lazy("Panel position %(number)s") % {"number": index},
                widget=forms.Select(attrs={"class": "input"}),
                choices=[("", gettext_lazy("Automatic order"))] + PANELS,
                required=False,
                initial=order[index - 1] if index <= len(order) else "",
            )

    def clean(self):
        values = super().clean()
        order = [values.get(f"position_{index}") for index in range(1, len(PANELS) + 1)]
        order = [item for item in order if item]
        if len(order) != len(set(order)):
            raise forms.ValidationError(
                gettext_lazy("Choose each panel only once in the order.")
            )
        values["order"] = order
        return values


def build_reports(account, filters, panel, *, query=None):
    data = build_report_data(account, filters, panel)
    preference = getattr(account.user, "fitness_preferences", None)
    presenter = DashboardPresenter(preference, query)
    charts = []
    for spec in data["charts"]:
        values, unit = convert_series(spec["values"], spec["unit"], preference)
        title = spec["title"]
        if "load_kg" in spec:
            load, load_unit = convert_series(
                {"load": spec["load_kg"]}, "kg", preference
            )
            from dashboard.presenters import _localized_number

            title += " · " + _localized_number(load["load"]) + " " + load_unit
        chart = presenter._categorical_chart(
            dom_id=spec["dom_id"],
            title=title,
            values=values,
            first_header=_("Observation"),
            unit=unit,
            kind=spec["kind"],
            temporal=spec["temporal"],
            target=spec.get("target"),
            partial_keys=spec.get("partial_keys", ()),
        )
        chart.update(
            {
                key: spec[key]
                for key in (
                    "definition",
                    "source_count",
                    "missing_count",
                    "formula_version",
                )
            }
        )
        charts.append(chart)
    data["charts"] = charts
    for comparison in data["comparisons"]:
        converted, unit = convert_series(
            {key: comparison[key] for key in ("current", "previous", "absolute")},
            comparison["unit"],
            preference,
        )
        comparison.update(converted)
        comparison["unit"] = unit
    for record in data["records"]:
        converted, unit = convert_series(
            {"value": record["value"]}, record["unit"], preference
        )
        record.update(converted)
        record["unit"] = unit
        record["date"] = date_label(record["at"], preference, include_time=True)
    return data
