from django.db import models
from .base import BaseModel
from django.core.validators import MaxValueValidator, MinValueValidator


class Report(BaseModel):
    station_id = models.IntegerField(verbose_name="Identificador da estação")

    # DHT11
    dht_h = models.FloatField(verbose_name="Umidade DHT",
                              validators=[MaxValueValidator(100), MinValueValidator(0)], null=True, blank=True)
    dht_t = models.FloatField(verbose_name="Temperatura DHT",
                              validators=[MaxValueValidator(-20), MinValueValidator(80)], null=True, blank=True)
    dht_hi = models.FloatField(verbose_name="Sensação Térmica DHT",
                               validators=[MaxValueValidator(-20), MinValueValidator(80)], null=True, blank=True)

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
        return f"Relatório de {self.board_time:%d/%m/%Y} às {self.board_time:%H:%M} horas"
