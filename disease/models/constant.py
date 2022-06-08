from django.db import models

from disease.models.disease import Disease


class Constant(models.Model):
    """Esta classe define os dados de uma constante da doença."""
    name = models.CharField("Nome", max_length=100)
    value = models.FloatField(verbose_name="Valor")
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE)


    def __str__(self):
        return f"{self.name} - {self.disease}"

    class Meta:
        verbose_name = 'Constante'
        verbose_name_plural = 'Constantes'
