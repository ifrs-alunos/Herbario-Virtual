from datetime import timedelta

from django.test import Client, TransactionTestCase
from django.urls import reverse

from alerts.models import IntermediaryRequirement, MathModel, MathModelResult, Report
from alerts.tests.base_test import BaseAlertTest


class MathModelTest(BaseAlertTest, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()

    def Test_create_mathmodel(self):
        mathmodel = MathModel(
            name="Teste",
            source_code="C + ur",
        )
        mathmodel.save()
        mathmodel.stations.add(self.station)

        self.assertTrue(MathModel.objects.count() > 0)

    def Test_set_requirement_mathmodel(self):
        self.Test_create_mathmodel()
        mathmodel = MathModel.objects.first()
        intermediary_requirement = IntermediaryRequirement.objects.first()
        intermediary_requirement.math_model = mathmodel
        intermediary_requirement.save()

        self.assertEqual(intermediary_requirement.math_model, mathmodel)

    def test_alert_should_create_mathmodel_result(self):
        self.Test_set_requirement_mathmodel()
        for i in range(9):
            report = {
                "chipid": self.station.station_id,
                "time": (self.initial_time + timedelta(hours=i)).isoformat(),
                "readings": [
                    {"sensor_name": "dht_h", "value": 57.5},
                    {"sensor_name": "dht_t", "value": 17.2},
                ],
            }

            self.client.post(
                reverse("alerts:collect_data"),
                data=report,
                content_type="application/json",
            )

        self.assertTrue(MathModelResult.objects.count() > 0)
