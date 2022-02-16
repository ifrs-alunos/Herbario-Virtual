from django import forms
from disease.models import PhotoDisease, Disease


class DiseasePhotoForm(forms.ModelForm):
	class Meta:
		model = PhotoDisease
		exclude = ['published']

	# Sobscrevendo o metodo clean pra retornar no form quando salvo um Disease object não um numero
	def clean(self):

		cleaned_data = super(DiseasePhotoForm, self).clean()
		cleaned_data['disease'] = Disease.objects.get(id=cleaned_data['disease'])
		return cleaned_data

	# Sobscrever o metodo __init__ para mostrar a cultura junto com o nome da doença
	def __init__(self, *args, **kwargs):
		super(DiseasePhotoForm, self).__init__(*args, **kwargs)
		queryset = Disease.objects.all()
		diseases = [(i.id, f'{i.name_disease} - {i.culture_disease}') for i in queryset]
		self.fields['disease'] = forms.ChoiceField(choices=diseases, label='Doença')
