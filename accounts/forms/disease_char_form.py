from django import forms
from accounts.models import CharSolicitationModel

class DiseaseCharSolicitationModelForm(forms.ModelForm):
    '''Formulário acessado por contribuidores para enviar uma solicitação de condição de desenvolvimento de uma doença nova'''

    class Meta:
        model = CharSolicitationModel
        exclude = ['slug']