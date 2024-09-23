from django.views.generic import DetailView
from alerts.models import MathModel
# SensorInMathModel

from django.utils import timezone
from datetime import datetime
from django.utils.timezone import localtime, make_aware
from alerts.forms import MathModelForm
from django.db.models import Avg
from plotly.offline import plot
import plotly.graph_objects as go
import datetime

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


def verify_require(requirements, value):
    r = [eval(re.replace("x", str(value))) for re in requirements]
    if False in r:
        return False
    else:
        return True


def get_reports(start, end, time_interval, requirements, mathmodel):
    # sensors_in_math = SensorInMathModel.objects.filter(mathmodel=mathmodel)
    sensors_in_math = ""
    data = {}
    data_x = []
    data_y = []
    sensors_in_graph = sensors_in_math.filter(in_graph=True).first()
    sensors_in_divider = sensors_in_math.filter(divider=True)

    data_in_graph = {}
    graphs = []

    for sensor_in_math in sensors_in_math:
        if sensor_in_math.mean:
            sensor = sensor_in_math.sensor
            re = requirements.filter(sensor=sensor)
            requires = [x.value_in_relation() for x in re]

            reports = (
                sensor.reading_set.filter(time__range=[start, end])
                .values("time")
                .annotate(avg_value=Avg("value"))
            )

            repo = [
                x["avg_value"] if verify_require(requires, x["avg_value"]) else 0
                for x in reports
            ]
            if sensor_in_math.in_graph:
                data_in_graph[sensor.type.name] = repo
            else:
                data[sensor.type.name] = repo
            data_x = [localtime(x["time"]) for x in reports]

    exp = mathmodel.source_code
    for key, value in mathmodel.constant_set.all().values_list("name", "value"):
        exp = exp.replace(key, str(value))

    value = 0
    sig_name = sensors_in_graph.sensor.type.name

    for y, x in enumerate(data_in_graph[sig_name]):
        for d in data:
            if x != 0 and data[d][y] != 0:
                exp_with_mean = exp
                exp_with_mean = exp_with_mean.replace(sig_name, str(x))
                eval_exp = eval(exp_with_mean).real

                value += eval_exp
                data_y.append(value)
            else:
                value = 0
                data_y.append(value)

    fig = go.Figure()
    fig.add_scatter(
        x=data_x,
        y=data_y,
        mode="lines",
        opacity=0.8,
        line={"color": colors[0]},
    )

    for x in sensors_in_divider:
        sensor = x.sensor
        sensor_name = sensor.type.name
        re = requirements.filter(sensor=sensor)
        requires = [x.value_in_relation() for x in re]
        reports = (
            sensor.reading_set.filter(time__range=[start, end])
            .values("time")
            .annotate(avg_value=Avg("value"))
        )
        for x in reports:
            if x["avg_value"] == 1:
                time_divider = localtime(x["time"])

                fig.add_vline(
                    x=time_divider.timestamp() * 1000,
                    line_width=3,
                    line_dash="dash",
                    line_color="green",
                    annotation_text=sensor_name,
                    annotation_font_size=20,
                )

    plot_element = plot(fig, output_type="div")

    return plot_element


class MathModelView(DetailView):
    model = MathModel
    template_name = "mathmodel.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = MathModelForm

        params = self.request.GET
        # se os parametros estiverem definidos, filtra a partir deles
        mathmodel = self.object
        requirements = mathmodel.requirement_set.all()
        sensors_type = list(set([x.sensor.id for x in requirements]))
        if params:
            start = datetime.fromisoformat(params.get("date_since"))
            start = make_aware(start, timezone=timezone.utc)
            end = datetime.fromisoformat(params.get("date_until"))
            end = make_aware(end, timezone=timezone.utc)

            # get_rp = get_reports_requirement_sensor_per_time_interval(Report, start, end, 5, sensors_type, requirements)
            get_rp = get_reports(start, end, 5, requirements, mathmodel)
        #
        # exp = mathmodel.source_code
        # for key, value in mathmodel.disease.constant_set.all().values_list('name', 'value'):
        # 	exp = exp.replace(key, str(value))
        #
        # data_in_graph = set_reports_data_to_graph(get_rp, exp)
        # se não, mostra os relatórios desde 12 horas atrás
        else:
            start = timezone.datetime(2022, 2, 1, 3, 0, 0, tzinfo=timezone.utc)
            end = timezone.datetime(2022, 3, 1, 2, 59, 59, tzinfo=timezone.utc)

            get_rp = get_reports(start, end, 15, requirements, mathmodel)
        # get_rp = get_reports_requirement_sensor_per_time_interval(Report, start, end, 5, sensors_type, requirements)
        # exp = mathmodel.source_code
        # for key, value in mathmodel.disease.constant_set.all().values_list('name', 'value'):
        # 	exp = exp.replace(key, str(value))

        # data_in_graph = set_reports_data_to_graph(get_rp, exp)

        plot_element = get_rp

        context["plot"] = plot_element

        return context
