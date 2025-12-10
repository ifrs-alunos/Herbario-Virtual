from django.db import models
from django.utils import timezone
from .base import BaseModel

class AlertHistory(BaseModel):
    math_model = models.ForeignKey(
        'MathModel',
        on_delete=models.CASCADE,
        verbose_name="Modelo Matemático"
    )
    station = models.ForeignKey(
        'Station', 
        on_delete=models.CASCADE,
        verbose_name="Estação"
    )
    alert_time = models.DateTimeField("Data/Hora do Alerta", default=timezone.now)
    alert_value = models.FloatField("Valor do Alerta")
    alert_message = models.TextField("Mensagem de Alerta")
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    details = models.TextField("Detalhes", blank=True)
    calculated_value = models.FloatField("Valor Calculado", null=True, blank=True)
    timestamp = models.DateTimeField("Timestamp", auto_now_add=True, null=True, blank=True)
    
    class Meta:
        verbose_name = "Histórico de Alerta"
        verbose_name_plural = "Históricos de Alertas"
        ordering = ['-alert_time']
    
    def __str__(self):
        return f"Alerta {math_model.name} - {station.alias}"