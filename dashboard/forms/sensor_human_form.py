from django import forms
from alerts.models import Reading


class SensorHumanForm(forms.ModelForm):
    choice = forms.BooleanField(label="Houve esporos?")

    class Meta:
        model = Reading
        fields = ['choice', 'time', 'sensor', 'value']
        widgets = {'sensor': forms.HiddenInput(), 'value': forms.HiddenInput()}
