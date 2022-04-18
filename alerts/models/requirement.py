from django.db import models
from .base import BaseModel
from .math_model import MathModel
from .sensor import Sensor
from .choices import RELATIONAL_TYPE_CHOICES


class Requirement(BaseModel):
	name = models.CharField('Nome', max_length=200, )
	value = models.IntegerField('Valor')
	math_model = models.ForeignKey(MathModel, on_delete=models.PROTECT, verbose_name='Modelo matematico')
	sensor = models.ForeignKey(Sensor, on_delete=models.PROTECT)
	relational = models.CharField(max_length=10, choices=RELATIONAL_TYPE_CHOICES, blank=True)
	requires = models.ManyToManyField("self", blank=True, symmetrical=False)

	def __str__(self):
		return f"{self.name} ─ {self.value} ─ {self.sensor}"

	class Meta:
		verbose_name = 'Requisito'
		verbose_name_plural = 'Requisitos'
