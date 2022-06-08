from django.views.generic import ListView

from alerts.views.utils import get_average_object_per_hour, to_datetime
from alerts.models import ReportOld, Formula
from alerts.forms import StationAndIntervalForm

import datetime

from plotly.offline import plot
from plotly.graph_objs import Bar


def generate_bar_graph(x_data, y_data):
    y_data_copy = []
    sum_ = 0
    for obj, condition_match in zip(x_data, y_data):
        if (obj.dht_h / 4095) >= 0.6:
            sum_ += condition_match
        else:
            sum_ = 0
        y_data_copy.append(sum_)

    return plot(
        [Bar(x=[i.board_time for i in x_data],
             y=y_data_copy)],
        output_type='div'
    )


class AlertsView(ListView):
    model = ReportOld
    context_object_name = "alerts"
    template_name = 'alerts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = StationAndIntervalForm()
        context['graph'] = generate_bar_graph(
            y_data=[i.get("condition_match") for i in self.get_queryset()],
            x_data=[i.get("obj") for i in self.get_queryset()],
        )
        return context

    def get_queryset(self):
        params = self.request.GET

        if params:
            datetime_since = to_datetime(params.get("date_since"), params.get("time_since"))
            datetime_until = to_datetime(params.get("date_until"), params.get("time_until"), until=True)
            average_object_per_hour = get_average_object_per_hour(ReportOld, datetime_since, datetime_until)
        # se não, mostra os relatórios desde 12 horas atrás
        else:
            average_object_per_hour = get_average_object_per_hour(
                ReportOld, datetime.datetime.now() - datetime.timedelta(days=120), datetime.datetime.now())

        condition_object = Formula.objects.first()
        return [{"obj": obj, "condition_match": obj.match_condition(condition_object)}
                for obj in average_object_per_hour]
