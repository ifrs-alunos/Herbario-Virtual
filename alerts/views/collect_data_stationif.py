from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from alerts.models import Station, Sensor, Report


@csrf_exempt
def collect_data_stationif(request):
    if request.method == 'POST':
        now = timezone.now()
        station = Station.objects.get(station_id=request.POST['chip_id'])
        dht_h = request.POST['dht_h']
        dht_t = request.POST['dht_t']
        ldr = request.POST['ldr']
        rain = float(request.POST['rain'])/4095
        soil = request.POST['soil']

        dht_h_station = Sensor.objects.get(type__name="dht_h")
        dht_t_station = station.sensor_set.get(type__name="dht_t")
        ldr_station = station.sensor_set.get(type__name="ldr")
        rain_station = station.sensor_set.get(type__name="rain")
        soil_station = station.sensor_set.get(type__name="soil")

        report_dht_h = Report(value=dht_h, time=now,sensor=dht_h_station)
        report_dht_t = Report(value=dht_t, time=now, sensor=dht_t_station)
        report_ldr = Report(value=ldr, time=now, sensor=ldr_station)
        report_rain = Report(value=rain, time=now, sensor=rain_station)
        report_soil = Report(value=soil, time=now, sensor=soil_station)

        report_dht_h.save()
        report_dht_t.save()
        report_ldr.save()
        report_rain.save()
        report_soil.save()

    return HttpResponse(":)")
