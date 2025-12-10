from django.db import models
from .base import BaseModel
from django.utils import timezone
from datetime import timedelta


class AnalysisWindow(BaseModel):
    """Controla a janela de análise para cada estação/modelo"""
    math_model = models.ForeignKey('MathModel', on_delete=models.CASCADE, verbose_name="Modelo matemático")
    station = models.ForeignKey('Station', on_delete=models.CASCADE, verbose_name="Estação")
    window_start = models.DateTimeField("Início da janela")
    window_end = models.DateTimeField("Fim da janela")
    reports_in_window = models.PositiveIntegerField("Relatórios na janela", default=0)
    valid_reports = models.PositiveIntegerField("Relatórios válidos", default=0)
    is_complete = models.BooleanField("Janela completa", default=False)
    accumulated_value = models.FloatField("Valor acumulado", default=0.0)
    
    class Meta:
        verbose_name = "Janela de Análise"
        verbose_name_plural = "Janelas de Análise"
        unique_together = ['math_model', 'station', 'window_start']
    
    def __str__(self):
        return f"{self.math_model.name} - {self.station.alias} - {self.window_start}"

class ConditionWindow(BaseModel):
    math_model = models.ForeignKey('MathModel', on_delete=models.CASCADE)
    station = models.ForeignKey('Station', on_delete=models.CASCADE)
    
    accumulation_start = models.DateTimeField("Início da acumulação", null=True)
    last_valid_report = models.DateTimeField("Último relatório válido", null=True)
    expected_alert_time = models.DateTimeField("Horário esperado do alerta", null=True)
    
    current_accumulated_value = models.FloatField("Valor acumulado atual", default=0.0)
    is_accumulation_active = models.BooleanField("Acumulação ativa", default=False)
    
    class Meta:
        unique_together = ['math_model', 'station']
    
    def __str__(self):
        status = "ATIVA" if self.is_accumulation_active else "INATIVA"
        return f"{self.math_model.name} - {self.station.alias} - {status} - {self.current_accumulated_value:.3f}"
    
    def should_trigger_alert(self, current_time=None):
        """Verifica se deve disparar alerta baseado no tempo esperado"""
        if not self.is_accumulation_active or not self.expected_alert_time:
            return False
        
        if current_time is None:
            current_time = timezone.now()
        
        return current_time >= self.expected_alert_time
    
    def get_remaining_time(self, current_time=None):
        """Retorna tempo restante para o alerta"""
        if not self.is_accumulation_active or not self.expected_alert_time:
            return None
        
        if current_time is None:
            current_time = timezone.now()
        
        if current_time >= self.expected_alert_time:
            return timedelta(0)
        
        return self.expected_alert_time - current_time

class HourlyResult(BaseModel):
    math_model = models.ForeignKey('MathModel', on_delete=models.CASCADE)
    station = models.ForeignKey('Station', on_delete=models.CASCADE)
    hour_start = models.DateTimeField("Início da hora")
    hour_end = models.DateTimeField("Fim da hora")
    value = models.FloatField("Valor calculado", default=0.0)
    accumulated_value = models.FloatField("Valor acumulado", default=0.0)
    requirements_met = models.BooleanField("Requisitos atendidos", default=False)
    
    class Meta:
        verbose_name = "Resultado Horário"
        verbose_name_plural = "Resultados Horários"
        unique_together = ['math_model', 'station', 'hour_start']
    
    def __str__(self):
        return f"{self.math_model.name} - {self.station.alias} - {self.hour_start}"