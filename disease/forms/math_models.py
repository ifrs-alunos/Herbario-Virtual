from django import forms
from disease.models import MathModels

class MathModelsForm(forms.ModelForm):
    class Meta:
        model = MathModels
        fields = '__all__'