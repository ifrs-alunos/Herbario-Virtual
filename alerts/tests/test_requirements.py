import datetime

from django.test import TestCase
from freezegun import freeze_time

from alerts.models import Reading, IntermediaryRequirement
from alerts.tests.base_test import BaseAlertTest, INITIAL_TIME


class RequirementTest(BaseAlertTest, TestCase):
    @freeze_time(INITIAL_TIME + datetime.timedelta(hours=6))
    def test_requirement_validation_is_true(self):
        objs = []
        for i in range(7):
            self.initial_time += datetime.timedelta(hours=i)
            objs.extend(
                [
                    Reading(sensor=self.t_sensor, value=20, time=self.initial_time),
                    Reading(sensor=self.rh_sensor, value=87, time=self.initial_time),
                ]
            )

        Reading.objects.bulk_create(objs)

        self.assertTrue(IntermediaryRequirement.objects.first().validate())

    @freeze_time(INITIAL_TIME + datetime.timedelta(hours=6))
    def test_requirement_validation_is_false(self):
        objs = []
        for i in range(3):
            self.initial_time += datetime.timedelta(hours=1)
            objs.extend(
                [
                    Reading(sensor=self.t_sensor, value=20, time=self.initial_time),
                    Reading(sensor=self.rh_sensor, value=87, time=self.initial_time),
                ]
            )

        self.initial_time += datetime.timedelta(hours=1)
        objs.extend(
            [
                Reading(sensor=self.t_sensor, value=20, time=self.initial_time),
                Reading(sensor=self.rh_sensor, value=84, time=self.initial_time),
            ]
        )

        for i in range(3):
            self.initial_time += datetime.timedelta(hours=1)
            objs.extend(
                [
                    Reading(sensor=self.t_sensor, value=20, time=self.initial_time),
                    Reading(sensor=self.rh_sensor, value=87, time=self.initial_time),
                ]
            )

        Reading.objects.bulk_create(objs)

        self.assertFalse(IntermediaryRequirement.objects.first().validate())
