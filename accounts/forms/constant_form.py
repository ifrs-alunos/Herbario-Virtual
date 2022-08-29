from django import forms
from django.core.exceptions import ValidationError

from alerts.models import Constant


class ConstantModelForm(forms.ModelForm):
    '''Formulário acessado por contribuidores para enviar uma constante do modelo matematico'''

    class Meta:
        model = Constant
        fields = '__all__'
        widgets = {'mathmodel': forms.HiddenInput()}

