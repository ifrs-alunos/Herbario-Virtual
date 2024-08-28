from django.db import models
from django.utils.timezone import localtime

from . import Sensor
from .base import BaseModel
from django.utils import timezone

from alerts.managers import AggregatorManager


class Report(BaseModel):
    time = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Relatório"
        verbose_name_plural = "Relatórios"
        ordering = ["time"]


class Reading(BaseModel):
    # AggregatorManager é uma classe que herda de   models.Manager, apenas adicionando a funcionalidade de agregação
    objects = AggregatorManager()

    value = models.FloatField("Valor", null=True)
    sensor = models.ForeignKey(Sensor, verbose_name="Sensor", on_delete=models.PROTECT)
    # mantido por retrocompatibilidade
    time = models.DateTimeField(default=timezone.now, null=True)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="readings", null=True)

    def __str__(self):
        return f"{self.sensor} - Valor: {self.value} -  Data: {localtime(self.time):%d/%m/%Y %H:%M} horas"

    @property
    def value_in_type(self):
        return eval(f"{self.sensor.type.metric}({self.value})")

    class Meta:
        verbose_name = "Leitura"
        verbose_name_plural = "Leituras"
        ordering = ["time"]
