from django.db import models
from . import Report

class TempReport(Report):
    identificator = models.IntegerField(verbose_name="Identificador")
