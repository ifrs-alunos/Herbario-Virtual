from django.utils.text import slugify
from .base import BaseModel
from django.db import models


class Station(BaseModel):
    station_id = models.CharField(
        max_length=20, verbose_name="Identificador da estação"
    )
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
            if sensor.report_set.last():
                sensor_report = sensor.report_set.last()  # Último report do sensor
                if sensor.type.metric == "bool":
                    sensor_value = float(sensor_report.value)
                    if sensor_value == 1.00:
                        return True
                    else:
                        return False

    def get_mathmodels_id(self):
        mathmodels_id = self.mathmodel_set.all().values_list("id", flat=True)
        return list(mathmodels_id)

    def __str__(self):
        return f"{self.alias} {self.lat_lon}"

    class Meta:
        verbose_name = "Estação"
        verbose_name_plural = "Estações"
