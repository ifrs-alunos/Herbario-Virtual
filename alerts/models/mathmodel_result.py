from django.db import models
from django.utils import timezone

from .base import BaseModel
from .math_model import MathModel

class MathModelResult(BaseModel):
    value = models.FloatField(verbose_name="Valor")
    date = models.DateTimeField(default=timezone.now)
    mathmodel = models.ForeignKey(MathModel, verbose_name="Modelo matematico", on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.mathmodel.name} - {self.date} = {self.value}"

    class Meta:
        verbose_name = 'Resultado de modelo matematico'
        verbose_name_plural = 'Resultado dos modelos matematicos'
