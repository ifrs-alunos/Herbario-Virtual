from django.contrib import admin

from .models import ReportOld, Station, Formula, Sensor, MathModel, Requirement, TypeSensor, Report
admin.site.register(ReportOld)
admin.site.register(Station)
admin.site.register(Formula)
admin.site.register(TypeSensor)
admin.site.register(Sensor)
admin.site.register(MathModel)
admin.site.register(Requirement)
admin.site.register(Report)
