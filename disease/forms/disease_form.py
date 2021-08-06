from django import forms
from disease.models import Disease

class DiseaseForm(forms.ModelForm):
    class Meta:
        model = Disease
        exclude = ['published']
