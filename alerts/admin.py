from django.contrib import admin

from .models import (
    Report,
    Station,
    Sensor,
    MathModel,
    Requirement,
    TypeSensor,
    Reading,
    SensorInMathModel,
    Constant,
    MathModelResult,
)

admin.site.register(Station)
admin.site.register(TypeSensor)
admin.site.register(Sensor)
admin.site.register(MathModel)
admin.site.register(Requirement)


@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = ("sensor", "value", "time", "report")
    search_fields = ("sensor__name", "time")
    list_filter = ("sensor", "time")

    ordering = ("-time",)


class ReadingInline(admin.TabularInline):
    model = Reading
    extra = 0


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("station", "time")
    search_fields = ("station", "time")
    list_filter = ("station", "time")
    inlines = [ReadingInline]

    ordering = ("-time",)


admin.site.register(SensorInMathModel)
admin.site.register(Constant)
admin.site.register(MathModelResult)
