from django.db import models
from .base import BaseModel
from .choices import SENSOR_TYPE_CHOICES


class Sensor(BaseModel):
    type = models.CharField(max_length=10, choices=SENSOR_TYPE_CHOICES, )

    def __str__(self):
        return f"{self.type}"

    class Meta:
        verbose_name = 'Sensor'
        verbose_name_plural = 'Sensores'