from django.contrib import admin

from .models import (
    Station,
    Formula,
    Sensor,
    MathModel,
    Requirement,
    TypeSensor,
    Report,
    SensorInMathModel,
    Constant,
    MathModelResult,
)

admin.site.register(Station)
admin.site.register(Formula)
admin.site.register(TypeSensor)
admin.site.register(Sensor)
admin.site.register(MathModel)
admin.site.register(Requirement)
admin.site.register(Report)
admin.site.register(SensorInMathModel)
admin.site.register(Constant)
admin.site.register(MathModelResult)
