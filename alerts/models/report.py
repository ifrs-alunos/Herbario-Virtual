from datetime import datetime

from django.db import models
from django.db.models import FloatField, Avg
from django.db.models.functions import TruncHour, Cast
from django.utils.timezone import localtime

from . import Sensor, MathModel
from .base import BaseModel
from django.utils import timezone


class Report(BaseModel):
	value = models.CharField('Valor', max_length=100, )
	sensor = models.ForeignKey(Sensor, verbose_name="Sensor", on_delete=models.PROTECT)
	time = models.DateTimeField(default=timezone.now)

	def __str__(self):
		return f"{self.sensor} - Valor: {self.value} -  Data: {localtime(self.time):%d/%m/%Y %H:%M} horas"

	@property
	def value_in_type(self):
		return eval(f'{self.sensor.type.metric}({self.value})')

	class Meta:
		verbose_name = 'Report'
		verbose_name_plural = 'Reports'
		ordering = ['time']
