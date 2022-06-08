from django.db import models
from django.utils import timezone
import math
from datetime import datetime
from django.utils.timezone import localtime, make_aware
from plotly.offline import plot
from plotly.graph_objs import Scatter

from . import Sensor
from .base import BaseModel
from disease.models.disease import Disease
from .report import Report
from django.db.models import QuerySet, Q
from django.utils.timezone import make_aware
from django.db.models import Avg
import time

colors = ("maroon", "orangered", "limegreen", "steelblue", "mediumblue", "indigo", "purple", "crimson", "darkred") * 2


# Função que pega todos os reports do sensor no range por time_interval
# tem umas gambiarras de localtime pq TIMEZONE

class MathModel(BaseModel):
	name = models.CharField('Nome do modelo matemático', max_length=100, blank=False,
							help_text='Insira o nome do modelo matemático')
	source_code = models.TextField(max_length=1000)
	disease = models.ForeignKey(Disease, verbose_name="Doença", on_delete=models.PROTECT)

	def __str__(self):
		return f"{self.name}"

	class Meta:
		verbose_name = 'Modelo matemático'
		verbose_name_plural = 'Modelos matemáticos'
