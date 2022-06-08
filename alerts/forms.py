from django import forms

from alerts.models import Station


class StationAndIntervalForm(forms.Form):
	station = forms.ModelChoiceField(queryset=Station.objects.all(), required=True)

	date_since = forms.DateTimeField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
	time_since = forms.DateTimeField(widget=forms.DateInput(attrs={'type': 'time'}), required=False)

	date_until = forms.DateTimeField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
	time_until = forms.DateTimeField(widget=forms.DateInput(attrs={'type': 'time'}), required=False)


class MathModelForm(forms.Form):
	date_since = forms.DateTimeField(label='Início', widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
	date_until = forms.DateTimeField(label='Fim', widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
	time_interval = forms.IntegerField(label='Intervalo de tempo em minutos')


class FormulaForm(forms.Form):
	name = forms.CharField(max_length=100, required=True)
	constants = forms.CharField(max_length=500, required=False, widget=forms.Textarea)
	expression = forms.CharField(max_length=1000, required=True, widget=forms.Textarea)
