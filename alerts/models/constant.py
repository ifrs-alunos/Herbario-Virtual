from django.db import models
from .math_model import MathModel


class Constant(models.Model):
    """Esta classe define os dados de uma constante da doença."""
    name = models.CharField("Nome", max_length=100)
    value = models.FloatField(verbose_name="Valor")
    mathmodel = models.ForeignKey(MathModel, on_delete=models.CASCADE, null=True)


    def __str__(self):
        return f"{self.name} - {self.mathmodel}"

    class Meta:
        verbose_name = 'Constante'
        verbose_name_plural = 'Constantes'
        managed = True
