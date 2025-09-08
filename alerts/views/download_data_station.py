# alerts/views/download_data_station.py
from datetime import datetime, time
import csv

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone

from alerts.forms import DownloadStationDataIntervalForm
from alerts.models import Station

def download_data_station(request, station_id):
    station = get_object_or_404(Station, station_id=station_id)
    sensors = station.sensor_set.all().order_by("name")
    error = ""

    form = DownloadStationDataIntervalForm(request.GET or None)

    if form.is_valid():
        date_since = form.cleaned_data["date_since"]  
        date_until = form.cleaned_data["date_until"]  

        tz = timezone.get_current_timezone()
        start_dt = datetime.combine(date_since, time.min)  
        end_dt = datetime.combine(date_until, time.max)    

        start_dt = timezone.make_aware(start_dt, tz)
        end_dt = timezone.make_aware(end_dt, tz)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="{date_since.isoformat()}__{date_until.isoformat()}.csv"'
        )
        writer = csv.writer(response)

        writer.writerow([station.alias])
        writer.writerow([])
        header = ["Data"] + [s.name for s in sensors]
        writer.writerow(header)

        relatorios_por_hora = {}
        for sensor in sensors:
            reports = sensor.reading_set.filter(time__range=(start_dt, end_dt)).order_by("time")
            for report in reports:
                hora = timezone.localtime(report.time).strftime("%Y-%m-%d %H:%M:%S")
                relatorios_por_hora.setdefault(hora, []).append(report.value)

        for hora in sorted(relatorios_por_hora):
            row = [hora] + relatorios_por_hora[hora]
            writer.writerow(row)

        if relatorios_por_hora:
            return response
        else:
            error = "Data indisponível."
    else:
        pass

    context = {"form": form, "error_message": error, "station": station}
    return render(request, "download_data_station.html", context)
