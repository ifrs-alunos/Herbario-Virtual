from django import forms
from alerts.models import MathModel


class MathModelForm(forms.ModelForm):
    '''Formulário acessado por contribuidores para enviar um modelo matematico'''

    class Meta:
        model = MathModel
        fields = '__all__'
