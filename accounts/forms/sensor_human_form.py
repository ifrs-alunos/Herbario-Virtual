from django import forms
from alerts.models import Report


class SensorHumanForm(forms.ModelForm):
	class Meta:
		model = Report
		fields = '__all__'
		exclude = ['sensor',]