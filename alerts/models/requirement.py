import logging

import numexpr
from django.db import models
from typing import List

from .base import BaseModel
from .math_model import MathModel
from .sensor import Sensor
from .choices import RELATIONAL_TYPE_CHOICES

logger = logging.getLogger("django")


class Requirement(BaseModel):
    name = models.CharField(
        "Nome",
        max_length=200,
    )
    sensor = models.ForeignKey(Sensor, on_delete=models.PROTECT)
    relational = models.CharField(
        max_length=10, choices=RELATIONAL_TYPE_CHOICES, blank=True, verbose_name="Operador relacional",
    )
    value = models.FloatField("Valor")
    requires = models.ManyToManyField("self", blank=True, symmetrical=False, verbose_name="Requisitos")

    # tempo mínimo em horas
    min_time = models.FloatField("Tempo mínimo", blank=True, null=True, help_text="Tempo mínimo em horas")

    def __str__(self):
        return f"{self.name} ({self.sensor.type} {self.relational} {self.value}) - {self.sensor.station}"

    def value_in_relation(self):
        return f"x {self.relational} {self.value}"

    def validate(self, exclude_ids: List[int] = None) -> bool:
        logger.info(f"Validating requirement {self}")
        if exclude_ids is None:
            exclude_ids = []
        if self.id not in exclude_ids:
            exclude_ids.append(self.id)

        for requirement in self.requires.all().exclude(id__in=exclude_ids):
            if not requirement.validate(exclude_ids=exclude_ids):
                logger.info(f"Requirement {requirement} failed")
                return False

        if not self.min_time:
            if not self.sensor.last_value:
                logger.info(f"Sensor {self.sensor} has no last value")
                return False
            logger.info(
                f"Validating requirement {self} with last value {self.sensor.last_value}, expression: {self.sensor.last_value} {self.relational} {self.value}")
            return numexpr.evaluate(
                f"{self.sensor.last_value} {self.relational} {self.value}"
            ).item(0)

        for hour in self.sensor.reading_set.aggregate_hours(self.min_time):
            logger.info(
                f"Validating requirement {self} with avg value {hour['avg_value']}, expression: {hour['avg_value']} {self.relational} {self.value}")
            if not numexpr.evaluate(
                    f"{hour['avg_value']} {self.relational} {self.value}"
            ).item(0):
                return False
        return True

    class Meta:
        verbose_name = "Requisito"
        verbose_name_plural = "Requisitos"


class IntermediaryRequirement(models.Model):
    name = models.CharField(
        "Nome",
        max_length=200,
    )
    requirements = models.ManyToManyField(Requirement, verbose_name="Requisitos")
    math_model = models.ForeignKey(
        MathModel,
        on_delete=models.PROTECT,
        verbose_name="Modelo matemático",
        blank=True,
        null=True,
    )

    @property
    def related_sensors(self) -> List[Sensor]:
        return [requirement.sensor for requirement in self.requirements.all()]

    def validate(self) -> bool:
        for requirement in self.requirements.all():
            if not requirement.validate():
                return False
        return True

    class Meta:
        verbose_name = "Requisito intermediário"
        verbose_name_plural = "Requisitos intermediários"
