from django import forms
from disease.models import PhotoDisease

class DiseasePhotoForm(forms.ModelForm):
    class Meta:
        model = PhotoDisease
        exclude = ['published']
