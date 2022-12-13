import datetime

from django.db.models.functions import ExtractDay, TruncMonth, Cast, TruncDay, TruncYear
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.timezone import localtime, make_aware

from alerts.forms import MathModelForm, ChooseMathModelForm
import plotly.graph_objects as go
from plotly.offline import plot
from django.db.models import Avg, FloatField
from plotly.subplots import make_subplots

from alerts.models import Station, Sensor

colors = ("maroon", "orangered", "limegreen", "steelblue", "mediumblue", "indigo", "purple", "crimson", "darkred") * 2


def get_sensor_data(request, sensor_id, date_filter):
    date = date_filter
    # last_report_date = timezone.make_aware(datetime.datetime.now(),timezone.get_default_timezone())
    sensor = Sensor.objects.get(id=sensor_id)
    last_report_date = sensor.report_set.all().last().time
    data_x=[]
    data_y=[]

    if date == "day":
        reports = sensor.report_set.filter(time__day=last_report_date.day,time__year=last_report_date.year,time__month=last_report_date.month).values('time', 'value')
        data_x = [localtime(x['time']) for x in reports]
        data_y = [x['value'] for x in reports]
    elif date == "week":
        # start_week = last_report_date - timezone.timedelta(last_report_date.weekday())
        # end_week = start_week + timezone.timedelta(7)
        end_week = last_report_date - timezone.timedelta(last_report_date.weekday())
        start_week = end_week - timezone.timedelta(7)
        reports = sensor.report_set.filter(time__range=[start_week, end_week]).values('time', 'value').annotate(
            value_float=Cast('value', output_field=FloatField())) \
            .annotate(day=TruncDay('time')) \
            .values('day') \
            .annotate(avg_value=Avg('value_float')) \
            .order_by("day")
        data_x = [localtime(x['day']) for x in reports]
        data_y = [x['avg_value'] for x in reports]
    elif date == "month":
        reports = sensor.report_set.filter(time__year=last_report_date.year).filter(time__month=last_report_date.month).annotate(
            value_float=Cast('value', output_field=FloatField())) \
            .annotate(day=TruncDay('time')) \
            .values('day') \
            .annotate(avg_value=Avg('value_float')) \
            .order_by("day")
        data_x = [localtime(x['day']) for x in reports]
        data_y = [x['avg_value'] for x in reports]

    elif date == "year":
        reports = sensor.report_set.filter(time__year=last_report_date.year).annotate(
            value_float=Cast('value', output_field=FloatField())) \
            .annotate(month=TruncMonth('time')) \
            .values('month') \
            .annotate(avg_value=Avg('value_float')) \
            .order_by("month")
        data_x = [localtime(x['month']) for x in reports]
        data_y = [x['avg_value'] for x in reports]
    elif date == "all":
        reports = sensor.report_set.annotate(
            value_float=Cast('value', output_field=FloatField())) \
            .annotate(year=TruncYear('time')) \
            .values('year') \
            .annotate(avg_value=Avg('value_float')) \
            .order_by("year")

        data_x = [localtime(x['year']) for x in reports]
        data_y = [x['avg_value'] if x['avg_value'] == x['avg_value'] else 0 for x in reports]
        # for para verificar caso exista alguma data com valor nulo retirar da lista
        for x, y in enumerate(data_y):
            if y == 0:
                data_x.pop(x)
                data_y.pop(x)

    else:
        data_x = []
        data_y = []

    return JsonResponse({'x': data_x, 'y': data_y})
