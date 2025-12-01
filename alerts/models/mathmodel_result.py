from django.db import models
from django.utils import timezone
from .base import BaseModel

class MathModelResult(BaseModel):
    value = models.FloatField(verbose_name="Valor")
    date = models.DateTimeField(default=timezone.now)
    mathmodel = models.ForeignKey(
        'alerts.MathModel', verbose_name="Modelo matemático", on_delete=models.PROTECT
    )
    station = models.ForeignKey(
        'alerts.Station', verbose_name="Estação", on_delete=models.PROTECT, null=True
    )
    accumulated_value = models.FloatField(
        "Valor Acumulado", 
        default=0.0,
        help_text="Soma acumulada dos valores até atingir o threshold"
    )
    is_alert_triggered = models.BooleanField(
        "Alerta disparado",
        default=False,
        help_text="Indica se este resultado disparou um alerta"
    )

    def __str__(self):
        return f"{self.mathmodel.name} - {self.station} - {self.accumulated_value:.2f}"

    class Meta:
        verbose_name = "Resultado de modelo matemático"
        verbose_name_plural = "Resultados dos modelos matemáticos"
        ordering = ["date"]