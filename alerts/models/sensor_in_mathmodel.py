from django.db import models
from .sensor import Sensor
from .base import BaseModel
from .math_model import MathModel


class SensorInMathModel(BaseModel):
    sensor = models.ForeignKey(Sensor, verbose_name="Sensor", on_delete=models.PROTECT)
    mathmodel = models.ForeignKey(
        MathModel, verbose_name="Modelo matemático", on_delete=models.PROTECT
    )
    divider = models.BooleanField(
        verbose_name="Usar como divisor",
        default=False,
        help_text="Marcar se este sensor deve ser usado como divisor no gráfico"
    )
    in_graph = models.BooleanField(
        verbose_name="Mostrar no gráfico",
        default=True,
        help_text="Marcar se este sensor deve ser exibido no gráfico principal"
    )
    mean = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sensor} - {self.mathmodel}"

    class Meta:
        unique_together = ('mathmodel', 'sensor')
        verbose_name = "Sensor no modelo matemático"
        verbose_name_plural = "Sensores nos modelos matemáticos"