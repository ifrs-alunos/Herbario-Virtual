from django.db import models

from . import Sensor
from .base import BaseModel
from .choices import METRIC_TYPE_CHOICES


class TypeSensor(BaseModel):
	name = models.CharField('Nome', max_length=100, )
	metric = models.CharField(max_length=10, choices=METRIC_TYPE_CHOICES, )
	sensor = models.ForeignKey(Sensor, verbose_name="Sensor", on_delete=models.PROTECT)

	def __str__(self):
		return f"{self.name} - {self.sensor}"

	class Meta:
		verbose_name = 'Tipo de Sensor'
		verbose_name_plural = 'Tipos de Sensores'
