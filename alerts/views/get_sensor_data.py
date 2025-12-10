from django.db import models
from django.db.models.functions import Coalesce, TruncMonth, Cast, TruncDay, TruncYear
from django.http import JsonResponse
from django.utils import timezone
from django.utils.timezone import localtime

from django.db.models import Avg, FloatField, Q

from alerts.models import Sensor

colors = (
    "maroon",
    "orangered",
    "limegreen",
    "steelblue",
    "mediumblue",
    "indigo",
    "purple",
    "crimson",
    "darkred",
) * 2


def get_sensor_data(request, sensor_id, date_filter):
    date = date_filter
    sensor = Sensor.objects.get(id=sensor_id)
    last_report_date = localtime(sensor.reading_set.last().time)
    if not last_report_date:
        last_report_date = localtime(sensor.reading_set.last().report.time)
    data_x = []
    data_y = []

    reports = sensor.reading_set.all().annotate(
        combined_time=Coalesce(
            "time", "report__time", output_field=models.DateTimeField()
        )
    )

    if date == "day":
        reports = reports.filter(
            combined_time__day=last_report_date.day,
            combined_time__year=last_report_date.year,
            combined_time__month=last_report_date.month,
        ).values("combined_time", "value")
        data_x = [localtime(x["combined_time"]) for x in reports]
        data_y = [x["value"] for x in reports]
    elif date == "week":
        end_week = last_report_date - timezone.timedelta(last_report_date.weekday())
        start_week = end_week - timezone.timedelta(7)
        reports = (
            sensor.reading_set.filter(time__range=[start_week, end_week])
            .values("time", "value")
            .annotate(value_float=Cast("value", output_field=FloatField()))
            .annotate(day=TruncDay("time"))
            .values("day")
            .annotate(avg_value=Avg("value_float"))
            .order_by("day")
        )
        data_x = [localtime(x["day"]) for x in reports]
        data_y = [x["avg_value"] for x in reports]
    elif date == "month":
        reports = (
            sensor.reading_set.filter(time__year=last_report_date.year)
            .filter(time__month=last_report_date.month)
            .annotate(value_float=Cast("value", output_field=FloatField()))
            .annotate(day=TruncDay("time"))
            .values("day")
            .annotate(avg_value=Avg("value_float"))
            .order_by("day")
        )
        data_x = [localtime(x["day"]) for x in reports]
        data_y = [x["avg_value"] for x in reports]

    elif date == "year":
        reports = (
            sensor.reading_set.filter(time__year=last_report_date.year)
            .annotate(value_float=Cast("value", output_field=FloatField()))
            .annotate(month=TruncMonth("time"))
            .values("month")
            .annotate(avg_value=Avg("value_float"))
            .order_by("month")
        )
        data_x = [localtime(x["month"]) for x in reports]
        data_y = [x["avg_value"] for x in reports]
    elif date == "all":
        reports = (
            sensor.reading_set.annotate(
                value_float=Cast("value", output_field=FloatField())
            )
            .annotate(year=TruncYear("time"))
            .values("year")
            .annotate(avg_value=Avg("value_float"))
            .order_by("year")
        )

        data_x = [localtime(x["year"]) for x in reports]
        data_y = [
            x["avg_value"] if x["avg_value"] == x["avg_value"] else 0 for x in reports
        ]
        for x, y in enumerate(data_y):
            if y == 0:
                data_x.pop(x)
                data_y.pop(x)

    else:
        data_x = []
        data_y = []

    if not (data_x and data_y):
        return JsonResponse({"x": [], "y": []}, status=404)

    sorted_data = sorted(zip(data_x, data_y))
    data_x, data_y = zip(*sorted_data)

    return JsonResponse({"x": data_x, "y": data_y}, status=200)
