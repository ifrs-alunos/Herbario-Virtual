from django.contrib import admin

from .models import Report, Station, Formula, Sensor, MathModel, Requirement

admin.site.register(Report)
admin.site.register(Station)
admin.site.register(Formula)
admin.site.register(Sensor)
admin.site.register(MathModel)
admin.site.register(Requirement)
