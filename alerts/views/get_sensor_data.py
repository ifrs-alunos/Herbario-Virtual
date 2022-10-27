from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.timezone import localtime, make_aware

from alerts.forms import MathModelForm, ChooseMathModelForm
import plotly.graph_objects as go
from plotly.offline import plot
from datetime import datetime
from django.db.models import Avg
from plotly.subplots import make_subplots

from alerts.models import Station, Sensor

colors = ("maroon", "orangered", "limegreen", "steelblue", "mediumblue", "indigo", "purple", "crimson", "darkred") * 2


def get_sensor_data(request, sensor_id):
    sensor = Sensor.objects.get(id=sensor_id)
    reports = sensor.report_set.filter().values('time', 'value')
    data_x = [localtime(x['time']) for x in reports]
    data_y = [x['value'] for x in reports]
    return JsonResponse({'x': data_x, 'y': data_y})
