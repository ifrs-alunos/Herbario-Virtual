from datetime import datetime

import pytz
from django.core.management.base import BaseCommand, CommandError
import pandas as pd
from django.utils import timezone

from alerts.models import Station, Sensor, TypeSensor, Report


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        # sensors_name = ["BattV_Min", "PTemp", "short_up_Avg", "short_dn_Avg", "long_up_Avg", "long_dn_Avg",
        #                 "cnr4_T_C_Avg", "cnr4_T_K_Avg", "long_up_corr_Avg", "long_dn_corr_Avg", "albedo_Avg",
        #                 "WS_ms_S_WVT", "WindDir_D1_WVT", "WindDir_SD1_WVT", "WS_ms_Max", "WS_ms_Min", "WindDir",
        #                 "AirTC_Avg", "AirTC_Max", "AirTC_Min", "RH", "AirTC_2_Avg", "AirTC_2_Max", "AirTC_2_Min",
        #                 "RH_2", "BP_mbar", "T108_C_Avg", "VW_Avg", "FlxSolo_Avg", "Rain_mm_Tot"]
        sensors_name = ["PTemp", "cnr4_T_C_Avg", "AirTC_Avg", "RH", "T108_C_Avg", "Rain_mm_Tot"]

        data = pd.read_csv("alerts/cepadi.csv")
        data['datahora'] = pd.to_datetime(data['datahora'])

        station_cepadi = Station.objects.get(station_id=23)
        list_sensors = []
        if not station_cepadi.sensor_set.all():
            for sensor in sensors_name:
                if sensor == "BattV_Min":
                    type_sensor_obj = TypeSensor(name=sensor, metric="v")
                if sensor == "PTemp":
                    type_sensor_obj = TypeSensor(name=sensor, metric="C")
                if sensor == "short_up_Avg" or sensor == "short_dn_Avg" or sensor == "long_up_Avg" or sensor == "long_dn_Avg":
                    type_sensor_obj = TypeSensor(name=sensor, metric="wm2")
                if sensor == "cnr4_T_C_Avg":
                    type_sensor_obj = TypeSensor(name=sensor, metric="C")
                if sensor == "cnr4_T_K_Avg":
                    type_sensor_obj = TypeSensor(name=sensor, metric="K")
                if sensor == "WS_ms_S_WVT" or sensor == "WindDir_D1_WVT" or sensor == "WindDir_SD1_WVT" or sensor == "WS_ms_Max" or sensor == "WS_ms_Min" or sensor == "WindDir":
                    type_sensor_obj = TypeSensor(name=sensor, metric="m/s")
                if sensor == "AirTC_Avg" or sensor == "AirTC_Max" or sensor == "AirTC_Min" or sensor == "AirTC_2_Avg" or sensor == "AirTC_2_Max" or sensor == "AirTC_2_Min":
                    type_sensor_obj = TypeSensor(name=sensor, metric="C")
                if sensor == "RH" or sensor == "RH_2":
                    type_sensor_obj = TypeSensor(name=sensor, metric="%")
                if sensor == "BP_mbar":
                    type_sensor_obj = TypeSensor(name=sensor, metric="mbar")
                if sensor == "T108_C_Avg":
                    type_sensor_obj = TypeSensor(name=sensor, metric="C")
                if sensor == "VW_Avg":
                    type_sensor_obj = TypeSensor(name=sensor, metric="%")
                if sensor == "Rain_mm_Tot":
                    type_sensor_obj = TypeSensor(name=sensor, metric="mm")
                if not Sensor.objects.filter(name=sensor).exists():
                    type_sensor_obj.save()
                else:
                    type_sensor_obj = Sensor.objects.get(name=sensor)
                sensor_obj = Sensor(name=sensor, type=type_sensor_obj, station=station_cepadi)
                list_sensors.append(sensor_obj)
        if not station_cepadi.sensor_set.all():
            Sensor.objects.bulk_create(list_sensors)
        datas = data['datahora'].tolist()
        col = 0
        print(sensors_name)
        for x in sensors_name:
            report_list = []
            sensor = Sensor.objects.get(name=x)

            for y in data[x][387770:]:
                local_tz = pytz.timezone('America/Sao_Paulo')

                dateteste = data['datahora'][col].replace(tzinfo=local_tz)
                report = Report(value=y, sensor=sensor, time=dateteste)
                report_list.append(report)
                col += 1
            col = 0
            Report.objects.bulk_create(report_list)
            print(f"Sensor {x} com reports! ")

        print("Acabou")
