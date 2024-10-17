import datetime

from alerts.models import IntermediaryRequirement, Requirement, Sensor, Station, TypeSensor
from django.utils.timezone import make_aware

INITIAL_TIME = make_aware(datetime.datetime(2024, 1, 1, 0, 0, 0))


class BaseAlertTest:
    station: Station
    rh_sensor: Sensor
    t_sensor: Sensor
    initial_time: datetime.datetime

    def setUp(self):
        self.station = Station.objects.create(station_id=185249135999496, slug="station", alias="Station",
                                              lat_coordinate=-28.503, lon_coordinate=-50.937)

        rh_sensor_type = TypeSensor.objects.create(name="dht_h", metric="ur")
        self.rh_sensor = Sensor.objects.create(name="rh_sensor", type=rh_sensor_type, station=self.station)

        t_sensor_type = TypeSensor.objects.create(name="dht_t", metric="C")
        self.t_sensor = Sensor.objects.create(name="t_sensor", type=t_sensor_type, station=self.station)

        self.initial_time = INITIAL_TIME

        intermediary_requirement = IntermediaryRequirement.objects.create(name="Intermediary requirement")

        lowest_temperature = Requirement.objects.create(
            name="Lowest temperature",
            sensor=self.t_sensor,
            relational=">=",
            value=15,
            min_time=6
        )
        lowest_temperature.save()
        intermediary_requirement.requirements.add(lowest_temperature)

        highest_temperature = Requirement.objects.create(
            name="Highest temperature",
            sensor=self.t_sensor,
            relational="<=",
            value=29,
            min_time=6
        )
        highest_temperature.save()
        intermediary_requirement.requirements.add(highest_temperature)

        minimum_humidity = Requirement.objects.create(
            name="Minimum humidity",
            sensor=self.rh_sensor,
            relational=">=",
            value=85,
            min_time=6
        )
        minimum_humidity.save()
        intermediary_requirement.requirements.add(minimum_humidity)
