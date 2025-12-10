from django.db import models
from .base import BaseModel
from alerts.managers import AggregatorManager
from django.utils.timezone import now

class Reading(BaseModel):
    value = models.FloatField("Valor", null=True)
    sensor = models.ForeignKey('Sensor', verbose_name="Sensor", on_delete=models.PROTECT)
    time = models.DateTimeField(default=now, null=True, verbose_name="Data", blank=True)
    report = models.ForeignKey(
        'Report',
        on_delete=models.CASCADE,
        related_name="readings",
        blank=True,
        null=True,
        verbose_name="Relatório",
    )

    class Meta:
        verbose_name = "Leitura"
        verbose_name_plural = "Leituras"
        ordering = ["time"]