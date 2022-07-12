from django import forms
from alerts.models import Report


class SensorHumanForm(forms.ModelForm):
	choice = forms.BooleanField(label="Houve esporos?")
	class Meta:
		model = Report
		fields = ['choice','time','sensor','value']
		widgets = {'sensor': forms.HiddenInput(),'value':forms.HiddenInput()}