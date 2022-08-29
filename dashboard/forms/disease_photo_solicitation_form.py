from django import forms
from ..models import DiseasePhotoSolicitation

class DiseasePhotoSolicitationModelForm(forms.ModelForm):
    '''Formulário acessado por contribuidores para enviar uma solicitação de nova foto de planta'''

    class Meta:
        model = DiseasePhotoSolicitation
        fields = '__all__'