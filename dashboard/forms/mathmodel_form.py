from django import forms
from alerts.models import MathModel

class MathModelForm(forms.ModelForm):
    constants = forms.CharField(
        label="Constantes",
        help_text="Formato: nome=valor;nome2=valor2 (ex: k1=0.5;temp_min=18)",
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'k1=0.5;k2=1.2',
            'class': 'form-control'
        })
    )
    
    source_code = forms.CharField(
        label="Fórmula Matemática",
        help_text="Use: t (temperatura), rh (umidade), rain (chuva). Exemplo: (t * k1) + (rh * k2)",
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': '(t * k1) + (rh * k2) - rain',
            'class': 'form-control'
        })
    )
    
    alert_threshold = forms.FloatField(
        label="Limite de Alerta",
        required=False,
        help_text="Valor que dispara alertas quando atingido",
        widget=forms.NumberInput(attrs={
            'step': '0.1',
            'class': 'form-control'
        })
    )
    
    alert_message = forms.CharField(
        label="Mensagem de Alerta",
        required=False,
        help_text="Use {value} para o valor calculado e {station} para o nome da estação",
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Alerta! Valor {value} atingido na estação {station}',
            'class': 'form-control'
        })
    )

    class Meta:
        model = MathModel
        fields = [
            'name', 'constants', 'source_code', 'disease', 'stations',
            'alert_threshold', 'alert_message', 'evaluation_period',
            'min_positive_reports', 'is_active', 'requirements'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'disease': forms.Select(attrs={'class': 'form-control'}),
            'stations': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'requirements': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'evaluation_period': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_positive_reports': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }