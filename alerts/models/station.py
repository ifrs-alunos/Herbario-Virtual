from django.utils.text import slugify
from typing import Dict

from .base import BaseModel
from django.db import models


class Station(BaseModel):
    station_id = models.CharField(max_length=20, verbose_name="Identificador da estação")
    slug = models.SlugField(unique=True, null=True)
    alias = models.CharField(max_length=100, verbose_name="Nome", null=True, blank=True)
    lat_coordinate = models.FloatField(verbose_name="Latitude", null=True)
    lon_coordinate = models.FloatField(verbose_name="Longitude", null=True)
    description = models.TextField(
        "Descrição da estação",
        max_length=400,
        help_text="Endereço, ponto de referência, responsável...",
        null=True,
    )

    @property
    def lat_lon(self):
        return [self.lat_coordinate, self.lon_coordinate]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.station_id)
        return super().save(*args, **kwargs)

    def get_human_sensor_condition(self):
        for sensor in self.sensor_set.all():
            if sensor.reading_set.last():
                sensor_report = sensor.reading_set.last()
                if sensor.type.metric == "human":
                    sensor_value = float(sensor_report.value)
                    return sensor_value == 1.00
        return False

    def get_mathmodels_id(self):
        mathmodels_id = self.mathmodel_set.all().values_list("id", flat=True)
        return list(mathmodels_id)

    def get_latest_readings(self) -> Dict[str, float]:
        sensors = self.sensor_set.all()
        readings = {}
    
        for sensor in sensors:
            if sensor.reading_set.last():
                if sensor.type.metric in ['dht_t', 'bmp_t']:
                    readings['t'] = sensor.last_value
                elif sensor.type.metric == 'dht_h':
                    readings['rh'] = sensor.last_value
                elif sensor.type.metric == 'rain':
                    readings['rain'] = sensor.last_value
    
        return readings

    def __str__(self):
        return f"{self.alias} {self.lat_lon}"

    class Meta:
        verbose_name = "Estação"
        verbose_name_plural = "Estações"