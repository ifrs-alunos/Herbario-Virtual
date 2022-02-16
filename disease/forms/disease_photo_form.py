from django import forms
from disease.models import PhotoDisease, Disease


class DiseasePhotoForm(forms.ModelForm):
	class Meta:
		model = PhotoDisease
		exclude = ['published']

	# Sobscrever o metodo __init__ para mostrar a cultura junto com o nome da doença
	def __init__(self, *args, **kwargs):
		super(DiseasePhotoForm, self).__init__(*args, **kwargs)
		queryset = Disease.objects.all()
		diseases = [(i.id, f'{i.name_disease} - {i.culture_disease}') for i in queryset]
		self.fields['disease'] = forms.ChoiceField(choices=diseases, label='Doença')
