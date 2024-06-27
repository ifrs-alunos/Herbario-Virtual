from django.db import models
from django.utils.timezone import localtime

from . import Sensor
from .base import BaseModel
from django.utils import timezone


class Report(BaseModel):
    value = models.FloatField("Valor", null=True)
    sensor = models.ForeignKey(Sensor, verbose_name="Sensor", on_delete=models.PROTECT)
    time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.sensor} - Valor: {self.value} -  Data: {localtime(self.time):%d/%m/%Y %H:%M} horas"

    @property
    def value_in_type(self):
        return eval(f"{self.sensor.type.metric}({self.value})")

    class Meta:
        verbose_name = "Report"
        verbose_name_plural = "Reports"
        ordering = ["time"]
