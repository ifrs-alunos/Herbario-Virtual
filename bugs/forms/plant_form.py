from django import forms
from herbarium.models import Plant

class PlantForm(forms.ModelForm):
    class Meta:
        model = Plant
        exclude = ['published']
