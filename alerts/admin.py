from django.contrib import admin

from .models import (
    Station,
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
admin.site.register(TypeSensor)
admin.site.register(Sensor)
admin.site.register(MathModel)
admin.site.register(Requirement)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("sensor", "value", "time")
    search_fields = ("sensor__name", "time")
    list_filter = ("sensor", "time")

    ordering = ("-time",)


admin.site.register(SensorInMathModel)
admin.site.register(Constant)
admin.site.register(MathModelResult)
