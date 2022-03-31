from django import forms
from django.forms import Select

from disease.models import Disease
from accounts.models import CharSolicitationModel


def get_char_choices():
	return [('-', '------------')] + [(x.id, x.__str__) for x in CharSolicitationModel.objects.all()]


class DiseaseForm(forms.ModelForm):
	class Meta:
		model = Disease
		exclude = ['published_disease']
		widgets = {
			'culture_disease': Select(attrs={'class': 'form-select'}),
		}
