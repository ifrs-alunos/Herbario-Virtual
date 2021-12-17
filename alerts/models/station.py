from django.utils.text import slugify

from .base import BaseModel
from django.db import models


class Station(BaseModel):
    station_id = models.IntegerField(verbose_name="Identificador da estação")
    slug = models.SlugField(unique=True)
    alias = models.CharField(max_length=100, verbose_name="Nome")
    lat_coordinate = models.FloatField(verbose_name="Latitude")
    lon_coordinate = models.FloatField(verbose_name="Longitude")

    @property
    def lat_lon(self):
        return [self.lat_coordinate, self.lon_coordinate]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.station_id)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.alias} {self.lat_lon}"

    class Meta:
        verbose_name = "Estação"
        verbose_name_plural = "Estações"
