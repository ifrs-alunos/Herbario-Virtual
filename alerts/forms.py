from django import forms
from accounts.models import Profile
from alerts.models import Station, MathModel, Station, Constant, Requirement
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


class AlertsForDiseasesForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["alerts_for_diseases"]

        widgets = {
            "alerts_for_diseases": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        profile = kwargs.pop("profile")
        super().__init__(*args, **kwargs)
        self.fields["alerts_for_diseases"].queryset = Disease.objects.filter(mathmodel__isnull=False)
        self.fields["alerts_for_diseases"].initial = profile.alerts_for_diseases.all()
        if profile:
            self.instance = profile



class StationForm(forms.ModelForm):
    class Meta:
        model = Station
        fields = ['station_id', 'alias', 'lat_coordinate', 'lon_coordinate', 'description']
        widgets = {
            'station_id': forms.TextInput(attrs={'class': 'form-control'}),
            'alias': forms.TextInput(attrs={'class': 'form-control'}),
            'lat_coordinate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'lon_coordinate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ConstantForm(forms.ModelForm):
    class Meta:
        model = Constant
        fields = ['name', 'value', 'mathmodel', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'mathmodel': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class RequirementForm(forms.ModelForm):
    class Meta:
        model = Requirement
        fields = ['name', 'parameter', 'operator', 'value', 'duration_hours', 'custom_expression', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'parameter': forms.Select(attrs={'class': 'form-control'}),
            'operator': forms.Select(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'duration_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'custom_expression': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }