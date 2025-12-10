import logging
import numexpr
from django.db import models
from django.db.models import Q
from .base import BaseModel

logger = logging.getLogger(__name__)

class Requirement(BaseModel):
    PARAMETER_CHOICES = [
        ('temperature', 'Temperatura'),
        ('humidity', 'Umidade'), 
        ('custom', 'Personalizado'),
    ]

    MATH_OPERATORS = [
        ('>', 'Maior que'),
        ('<', 'Menor que'),
        ('>=', 'Maior ou igual'),
        ('<=', 'Menor ou igual'),
        ('==', 'Igual a'),
        ('!=', 'Diferente de'),
    ]

    name = models.CharField(
        "Nome do requisito",
        max_length=200,
        help_text="Nome descritivo para identificar o requisito"
    )
    parameter = models.CharField(
        "Parâmetro",
        max_length=20,
        choices=PARAMETER_CHOICES,
        help_text="Parâmetro meteorológico a ser verificado"
    )
    operator = models.CharField(
        "Operador", 
        max_length=3,
        choices=MATH_OPERATORS,
        help_text="Operador de comparação"
    )
    value = models.FloatField("Valor de referência", help_text="Valor limite para comparação")
    duration_hours = models.FloatField(
        "Duração mínima (horas)",
        null=True,
        blank=True,
        help_text="Tempo mínimo que a condição deve ser mantida (opcional)"
    )
    custom_expression = models.TextField(
        "Expressão personalizada",
        blank=True,
        help_text="Expressão customizada usando variáveis: t, rh, rain"
    )
    is_active = models.BooleanField("Ativo", default=True, help_text="Se desmarcado, este requisito será ignorado")

    class Meta:
        verbose_name = "Requisito"
        verbose_name_plural = "Requisitos"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_parameter_display()} {self.operator} {self.value})"

    def validate_for_report(self, report):
        try:
            sensor_data = report.get_sensor_data()
            
            print(f"🔍 Validando requisito {self.name}:")
            print(f"   Parâmetro: {self.parameter}, Operador: {self.operator}, Valor: {self.value}")
            print(f"   Dados: t={sensor_data['t']}, rh={sensor_data['rh']}")
            
            if self.parameter == 'temperature' and sensor_data['t'] is not None:
                temp = sensor_data['t']
                value = self.value
                
                if self.operator == '>': result = temp > value
                elif self.operator == '<': result = temp < value
                elif self.operator == '>=': result = temp >= value
                elif self.operator == '<=': result = temp <= value
                elif self.operator == '==': result = temp == value
                elif self.operator == '!=': result = temp != value
                else: result = False
                    
                print(f"   Comparação: {temp} {self.operator} {value} = {result}")
                return result
                
            elif self.parameter == 'humidity' and sensor_data['rh'] is not None:
                humidity = sensor_data['rh']
                value = self.value
                
                if self.operator == '>': result = humidity > value
                elif self.operator == '<': result = humidity < value
                elif self.operator == '>=': result = humidity >= value
                elif self.operator == '<=': result = humidity <= value
                elif self.operator == '==': result = humidity == value
                elif self.operator == '!=': result = humidity != value
                else: result = False
                    
                print(f"   Comparação: {humidity} {self.operator} {value} = {result}")
                return result
            
            print(f"❌ Não foi possível validar requisito {self.name}")
            return False
            
        except Exception as e:
            print(f"❌ Erro ao validar requisito {self.name}: {e}")
            return False

    def _validate_standard_requirement(self, report) -> bool:
        param_mapping = {
            'temperature': {
                'fields': ['temperatura', 'reading_temp'],
                'name': 'Temperatura'
            },
            'humidity': {
                'fields': ['umidade', 'reading_humidity'], 
                'name': 'Umidade'
            },
        }
        
        param_info = param_mapping.get(self.parameter)
        if not param_info:
            return False
            
        report_value = None
        for field_name in param_info['fields']:
            if hasattr(report, field_name):
                value = getattr(report, field_name, None)
                if value is not None:
                    report_value = value
                    break
        
        if report_value is None:
            return False

        try:
            report_value = float(report_value)
            expression = f"{report_value} {self.operator} {self.value}"
            result = eval(expression)
            return bool(result)
        except (TypeError, ValueError, Exception):
            return False

    def _validate_custom_expression(self, report) -> bool:
        try:
            local_dict = {
                't': report.temperatura or 0,
                'rh': report.umidade or 0,
                'rain': report.tempo_chuva or 0
            }
            result = numexpr.evaluate(self.custom_expression, local_dict=local_dict).item()
            return bool(result)
        except Exception:
            return False

    def get_filter_condition(self):
        field_mapping = {
            'temperature': 'temperatura',
            'humidity': 'umidade',
        }
        
        field_name = field_mapping.get(self.parameter)
        if not field_name:
            return Q()
        
        operator_mapping = {
            '>': '__gt',
            '>=': '__gte',
            '<': '__lt', 
            '<=': '__lte',
            '==': '',
            '!=': '__ne'
        }
        
        lookup = operator_mapping.get(self.operator, '')
        filter_kwarg = f"{field_name}{lookup}" if lookup else field_name
        
        return Q(**{filter_kwarg: self.value})

    @property
    def field_name(self):
        field_mapping = {
            'temperature': 'temperatura',
            'humidity': 'umidade',
        }
        return field_mapping.get(self.parameter, '')