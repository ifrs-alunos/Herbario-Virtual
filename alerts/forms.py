from django import forms
from django.utils import timezone

from accounts.models import Profile
from alerts.models import Station, MathModel
from disease.models import Disease

class StationAndIntervalForm(forms.Form):
    station = forms.ModelChoiceField(queryset=Station.objects.all(), required=True)

    date_since = forms.DateTimeField(
        widget=forms.DateInput(attrs={"type": "date"}), required=True
    )
    time_since = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "time"}), required=False
    )

    date_until = forms.DateTimeField(
        widget=forms.DateInput(attrs={"type": "date"}), required=False
    )
    time_until = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "time"}), required=False
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
    date_since = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),label="Data Início",input_formats=["%Y-%m-%d"],required=True,
    )
    date_until = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),label="Data Fim",input_formats=["%Y-%m-%d"],required=False,
    )

    def clean_date_until(self):
        date_until = self.cleaned_data.get("date_until")
        if date_until is None: 
            return timezone.localdate()
        return date_until
    
    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("date_since")
        end = cleaned.get("date_until")
        if start and end and end < start:
            raise forms.ValidationError("Data final não pode ser anterior à data inicial.")
        return cleaned


class AlertsForDiseasesForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["alerts_for_diseases"]

        widgets = {
            "alerts_for_diseases": forms.CheckboxSelectMultiple,
        }

