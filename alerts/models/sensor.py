from django.db import models

from . import Station
from .base import BaseModel
from .choices import SENSOR_TYPE_CHOICES, METRIC_TYPE_CHOICES


class Sensor(BaseModel):
	type = models.CharField(max_length=10, choices=SENSOR_TYPE_CHOICES, )
	metric = models.CharField(max_length=10, choices=METRIC_TYPE_CHOICES, )
	station = models.ForeignKey(Station, verbose_name="Estação", on_delete=models.PROTECT, null=True, blank=True)

	def __str__(self):
		return f"{self.type} - {self.station}"

	class Meta:
		verbose_name = 'Sensor'
		verbose_name_plural = 'Sensores'
