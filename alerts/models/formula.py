from django.db import models

from alerts.models import BaseModel


class Formula(BaseModel):
    name = models.CharField(max_length=100)
    constants = models.JSONField()
    expression = models.TextField(max_length=1000)
