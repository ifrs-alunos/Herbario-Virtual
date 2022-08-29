from django import forms
from ..models import DiseaseSolicitation

class DiseaseSolicitationModelForm(forms.ModelForm):
    '''Formulário acessado por contribuidores para enviar uma solicitação de doença nova'''

    class Meta:
        model = DiseaseSolicitation
        fields = '__all__'