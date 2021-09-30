from django import forms
from accounts.models import PhotoSolicitation

class PhotoSolicitationModelForm(forms.ModelForm):
    '''Formulário acessado por contribuidores para enviar uma solicitação de nova foto de planta'''

    class Meta:
        model = PhotoSolicitation
        fields = '__all__'