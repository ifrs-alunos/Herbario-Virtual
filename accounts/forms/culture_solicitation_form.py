from django import forms
from disease.models import Culture


class CultureSolicitationModelForm(forms.ModelForm):
    '''Formulário acessado por contribuidores para enviar uma solicitação de condição de desenvolvimento de uma
    doença nova '''

    class Meta:
        model = Culture
        fields = '__all__'
        exclude = ['icon', ]
