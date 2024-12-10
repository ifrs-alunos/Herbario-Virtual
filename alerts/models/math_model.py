import numexpr
from django.db import models
from typing import Dict

from alerts.models.mathmodel_result import MathModelResult
from alerts.models.station import Station
from .base import BaseModel
from disease.models.disease import Disease


class MathModel(BaseModel):
    name = models.CharField(
        "Nome do modelo matemático",
        max_length=100,
        blank=False,
        help_text="Insira o nome do modelo matemático",
    )
    source_code = models.TextField(
        max_length=1000,
        help_text="Variaveis disponiveis no momento: t = Temperatura rh = "
                  "Umidade Relativa</h4>",
    )
    disease = models.ForeignKey(
        Disease, verbose_name="Doença", on_delete=models.PROTECT, null=True, blank=True
    )
    stations = models.ManyToManyField(
        Station, verbose_name="Estaçôes atreladas", blank=True
    )

    def __str__(self):
        return f"{self.name}"

    def get_constants_dict(self) -> Dict[str, float]:
        constants = self.constant_set.all()

        return {constant.name: constant.value for constant in constants}

    def evaluate_by_station(self, station: Station) -> MathModelResult:
        """
        Evaluate the math model for a given station and return the result
        """

        local_dict = station.get_latest_readings() | self.get_constants_dict()

        value = numexpr.evaluate(self.source_code, local_dict=local_dict).item(0)
        result = MathModelResult(value=value, mathmodel=self)
        result.save()

        return result

    class Meta:
        verbose_name = "Modelo matemático"
        verbose_name_plural = "Modelos matemáticos"
