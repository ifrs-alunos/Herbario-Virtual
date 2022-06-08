from django.db import models
from alerts.models import Formula
from .base import BaseModel
from django.core.validators import MaxValueValidator, MinValueValidator

from .station import Station


class ReportOld(BaseModel):
    station = models.ForeignKey(Station, verbose_name="Estação", on_delete=models.PROTECT, null=True, blank=True)
    station_identificator = models.IntegerField(verbose_name="Identificador da estação")

    # DHT11
    dht_h = models.FloatField(verbose_name="Umidade DHT",
                              validators=[MaxValueValidator(100), MinValueValidator(0)], null=True, blank=True)
    dht_t = models.FloatField(verbose_name="Temperatura DHT",
                              validators=[MaxValueValidator(100), MinValueValidator(-20)], null=True, blank=True)
    dht_hi = models.FloatField(verbose_name="Sensação Térmica DHT",
                               validators=[MaxValueValidator(100), MinValueValidator(-20)], null=True, blank=True)

    # BMP280
    bmp_t = models.FloatField(verbose_name="Temperatura BMP",
                              validators=[MaxValueValidator(-20), MinValueValidator(80)], null=True, blank=True)
    bmp_p = models.FloatField(verbose_name="Pressão BMP", null=True, blank=True)
    bmp_a = models.FloatField(verbose_name="Altitude BMP", null=True, blank=True)

    # LDR
    ldr = models.IntegerField(verbose_name="Luz LDR", null=True, blank=True)

    # rain
    rain = models.IntegerField(verbose_name="Chuva", null=True, blank=True)

    # soil moisture
    soil = models.IntegerField(verbose_name="Umidade do solo", null=True, blank=True)

    # ultraviolet light
    uv = models.FloatField(verbose_name="Luz UV", null=True, blank=True)

    # client-side report time
    board_time = models.DateTimeField()

    def __str__(self):
        try:
            return f"{self.station.alias} ─ {self.board_time:%d/%m/%Y} às {self.board_time:%H:%M} horas"
        except Exception:
            return "Aferição"

    def save(self, *args, **kwargs):
        if not self.station:
            station = Station.objects.get(station_id=self.station_identificator)
            if not station:
                station = Station.objects.create(station_id=self.station_identificator,
                                                 alias=self.station_identificator)
                station.save()

            self.station = station

        super().save(*args, **kwargs)

    def match_condition(self, condition: Formula) -> float:
        import math
        exp = condition.expression
        for key, value in condition.constants.items():
            exp = exp.replace(key, str(value))
        return eval(exp)
