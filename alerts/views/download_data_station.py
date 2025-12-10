from datetime import datetime, timezone
import csv

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.timezone import make_aware, localtime

from alerts.forms import DownloadStationDataIntervalForm
from alerts.models import Station


def download_data_station(request, station_id):
    station = Station.objects.get(station_id=station_id)
    sensors = station.sensor_set.all().order_by("name")
    error = ""
    if request.GET.get("date_since") is not None:
        start = datetime.fromisoformat(request.GET.get("date_since"))
        start = make_aware(start, timezone=timezone.utc)
        end = datetime.fromisoformat(request.GET.get("date_until"))
        end = make_aware(end, timezone=timezone.utc)
        response = HttpResponse(
            content_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{start.strftime("%Y-%m-%d %H:%M:%S")}.csv"'
            },
        )
        writer = csv.writer(response)
        sensors_name = ["Data"]
        writer.writerow(
            [
                station.alias,
            ]
        )
        writer.writerow(" ")
        for x in sensors:
            sensors_name.append(x.name)
        writer.writerow(sensors_name)

        relatorios_por_hora = {}
        for sensor in sensors:
            reports = sensor.reading_set.all().filter(time__range=(start, end))
            for report in reports:
                hora = localtime(report.time).strftime("%Y-%m-%d %H:%M:%S")
                if hora not in relatorios_por_hora:
                    relatorios_por_hora[hora] = []
                relatorios_por_hora[hora].append(report.value)

        for x in relatorios_por_hora:
            row = [x]
            for relatorio in relatorios_por_hora[x]:
                row.append(relatorio)
            writer.writerow(row)

        if relatorios_por_hora:
            return response
        else:
            error = "Data indisponível"
    else:
        pass

    form_interval = DownloadStationDataIntervalForm()
    context = {"form": form_interval, "error_message": error}

    return render(request, "download_data_station.html", context)
