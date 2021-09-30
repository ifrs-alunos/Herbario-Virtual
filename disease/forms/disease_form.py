from django import forms
from disease.models import Disease
from accounts.models import  CharSolicitationModel

def get_char_choices():
    return [('-', '------------')]+[(x.id, x.__str__()) for x in CharSolicitationModel.objects.all()]

class DiseaseForm(forms.ModelForm):

    class Meta:
        model = Disease
        exclude = ['published_disease']
