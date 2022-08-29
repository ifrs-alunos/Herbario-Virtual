from django import forms
from django.forms import Select

from disease.models import Disease


class DiseaseForm(forms.ModelForm):
	class Meta:
		model = Disease
		exclude = ['published_disease']
		widgets = {
			'culture_disease': Select(attrs={'class': 'form-select'}),
		}
