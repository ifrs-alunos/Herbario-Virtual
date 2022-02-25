from django import forms

from alerts.models import Station


class StationAndIntervalForm(forms.Form):
    station = forms.ModelChoiceField(queryset=Station.objects.all(), required=True)

    date_since = forms.DateTimeField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    time_since = forms.DateTimeField(widget=forms.DateInput(attrs={'type': 'time'}), required=False)

    date_until = forms.DateTimeField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    time_until = forms.DateTimeField(widget=forms.DateInput(attrs={'type': 'time'}), required=False)
