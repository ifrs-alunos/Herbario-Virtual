from .base import BaseModel
from django.db import models


class Station(BaseModel):
    station_id = models.IntegerField(verbose_name="Identificador da estação")
    alias = models.CharField(max_length=100, verbose_name="Nome")
    lat_coordinate = models.FloatField(verbose_name="Latitude")
    lon_coordinate = models.FloatField(verbose_name="Longitude")

    class Meta:
        verbose_name = "Estação"
        verbose_name_plural = "Estações"
