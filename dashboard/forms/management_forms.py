from django import forms
from alerts.models import Station, Constant, Requirement

class StationForm(forms.ModelForm):
    class Meta:
        model = Station
        fields = ['station_id', 'alias', 'lat_coordinate', 'lon_coordinate', 'description']
        widgets = {
            'station_id': forms.TextInput(attrs={'class': 'form-control'}),
            'alias': forms.TextInput(attrs={'class': 'form-control'}),
            'lat_coordinate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'lon_coordinate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'station_id': 'ID da Estação',
            'alias': 'Nome/Alias',
            'lat_coordinate': 'Latitude',
            'lon_coordinate': 'Longitude',
            'description': 'Descrição'
        }

class ConstantForm(forms.ModelForm):
    class Meta:
        model = Constant
        fields = ['name', 'value', 'mathmodel', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'mathmodel': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'name': 'Nome da Constante',
            'value': 'Valor',
            'mathmodel': 'Modelo Matemático',
            'description': 'Descrição'
        }

class RequirementForm(forms.ModelForm):
    class Meta:
        model = Requirement
        fields = ['name', 'parameter', 'operator', 'value', 'duration_hours', 'custom_expression', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'parameter': forms.Select(attrs={'class': 'form-control'}),
            'operator': forms.Select(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'duration_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'custom_expression': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Exemplo: (t > 25) and (rh < 80)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Nome do Requisito',
            'parameter': 'Parâmetro',
            'operator': 'Operador',
            'value': 'Valor de Referência',
            'duration_hours': 'Duração Mínima (horas)',
            'custom_expression': 'Expressão Personalizada',
            'is_active': 'Ativo'
        }
        help_texts = {
            'custom_expression': 'Use variáveis: t (temperatura), rh (umidade), rain (chuva)',
            'duration_hours': 'Tempo mínimo que a condição deve ser mantida (opcional)',
        }