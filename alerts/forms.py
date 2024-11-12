from django import forms

from alerts.models import Station, MathModel, UserAlert
from disease.models import Disease


class StationAndIntervalForm(forms.Form):
    station = forms.ModelChoiceField(queryset=Station.objects.all(), required=True)

    date_since = forms.DateTimeField(
        widget=forms.DateInput(attrs={"type": "date"}), required=True
    )
    time_since = forms.DateTimeField(
        widget=forms.DateInput(attrs={"type": "time"}), required=False
    )

    date_until = forms.DateTimeField(
        widget=forms.DateInput(attrs={"type": "date"}), required=False
    )
    time_until = forms.DateTimeField(
        widget=forms.DateInput(attrs={"type": "time"}), required=False
    )


class MathModelForm(forms.Form):
    date_since = forms.DateTimeField(
        label="Início", widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    date_until = forms.DateTimeField(
        label="Fim", widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )


class ChooseMathModelForm(forms.Form):
    mathmodel = forms.ModelMultipleChoiceField(
        queryset=MathModel.objects.all(), label="Modelos matemáticos"
    )


class DownloadStationDataIntervalForm(forms.Form):
    date_since = forms.DateTimeField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Data Inicio",
        required=True,
    )
    date_until = forms.DateTimeField(
        widget=forms.DateInput(attrs={"type": "date"}), label="Data Fim", required=False
    )


class UserAlertForm(forms.Form):
    disease = forms.ModelMultipleChoiceField(
        queryset=Disease.objects.filter(mathmodel__isnull=False),
        widget=forms.CheckboxSelectMultiple(),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(UserAlertForm, self).__init__(*args, **kwargs)
        self.fields["disease"].queryset = Disease.objects.filter(
            mathmodel__isnull=False
        )
        if user:
            user_alerts = UserAlert.objects.filter(profile=user.profile)
            self.initial["disease"] = [alert.disease.id for alert in user_alerts]
