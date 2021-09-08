from django import forms
from core.models import Colaborators

class ColaboratorsModelForm(forms.ModelForm):
    '''Formulário acessado por contribuidores para enviar uma solicitação de doença nova'''

    class Meta:
        model = Colaborators
        fields = '__all__'