from django import forms
from accounts.models import PlantSolicitation

class PlantSolicitationModelForm(forms.ModelForm):
    '''Formulário acessado por contribuidores para enviar uma solicitação de planta nova'''

    class Meta:
        model = PlantSolicitation
        fields = '__all__'