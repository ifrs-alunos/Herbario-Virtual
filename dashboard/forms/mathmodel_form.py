from django import forms

from alerts.models import MathModel


class MathModelForm(forms.ModelForm):
    constants = forms.CharField(label="Constantes",help_text="deve digitar nesse formato: "
                                                             "constante=valor;constante2=valor2")

    class Meta:
        model = MathModel
        fields = ['name', 'constants', 'source_code', 'disease', 'stations']
