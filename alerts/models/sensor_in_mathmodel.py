from django.db import models

from . import Sensor, MathModel
from .base import BaseModel


class SensorInMathModel(BaseModel):
    sensor = models.ForeignKey(Sensor, verbose_name="Sensor", on_delete=models.PROTECT)
    mathmodel = models.ForeignKey(
        MathModel, verbose_name="Modelo matemático", on_delete=models.PROTECT
    )
    divider = models.BooleanField(verbose_name="Usar como um divisor?")

    def __str__(self):
        return f"{self.sensor} - {self.mathmodel}"

    class Meta:
        verbose_name = "Sensor no modelo matematico"
        verbose_name_plural = "Sensores nos modelos matematicos"
