from django import forms
from core.models import Publication


class PublicationForm(forms.ModelForm):
	class Meta:
		model = Publication
		fields = '__all__'
		exclude = ['slug',]
