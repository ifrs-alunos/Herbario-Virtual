import re
from itertools import groupby, chain

import numexpr
from django.db.models import Q, Avg, F
from django.db.models.functions import TruncDate, TruncHour, Cast
from django.db.models import Avg, FloatField
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.timezone import localtime
from django.db.models import QuerySet
from django.views.generic import CreateView, UpdateView, ListView, DeleteView

from ..forms import MathModelForm
from ..forms.sensor_human_form import SensorHumanForm
from operator import attrgetter
from alerts.models import MathModel, Sensor, Constant, MathModelResult, Report


def _create_constants(constants_string: str, saved_form) -> None:
    constants = constants_string.split(";")
    for constant in constants:
        if constant != '':
            name, value = constant.split("=")
            new_constant = Constant(name=name, value=value, mathmodel=saved_form)
            new_constant.save()


def _replace_values(exp: str, values_dict: dict) -> str:
    # Tokens se refere a cada "elemento" na expressão, seja um operador, um número, uma variável, etc.
    tokens = re.split(r'(\W+)', exp)

    new_tokens = [values_dict.get(token, token) for token in tokens]

    return "".join(new_tokens)


class MathModelFormMixin:
    model = MathModel
    form_class = MathModelForm

    template_name = 'dashboard/mathmodel_create_form.html'
    success_url = reverse_lazy('dashboard:mathmodel_update')

    def validate_form(self, form: MathModelForm) -> None:
        math_model: MathModel = form.save()
        math_model.constant_set.all().delete()
        math_model.mathmodelresult_set.all().delete()
        _create_constants(form.cleaned_data['constants'], math_model)

        constants_dict = {name: str(value) for name, value in math_model.constant_set.values_list('name', 'value')}

        exp = _replace_values(math_model.source_code, constants_dict)

        list_results = []

        for station in math_model.stations.all():
            """
            reports_by_hour é um dicionário no seguinte formato:
            {
                datetime1: { sensor1: value1, sensor2: value2, ... },
                datetime2: { sensor1: value1, sensor2: value2, ... },
                ...
            """
            reports_by_hour = {}

            for sensor in station.sensor_set.all():
                name = sensor.type.name

                reports = sensor.report_set \
                    .annotate(hour=TruncHour('time', is_dst=False)) \
                    .values('hour') \
                    .annotate(avg_value=Avg('value')) \
                    .order_by("hour")

                for report in reports:
                    hour = report['hour']

                    if reports_by_hour.get(hour) is None:
                        reports_by_hour[hour] = {}

                    reports_by_hour[hour][name] = report['avg_value']

            condition = 0

            for hour, reports in reports_by_hour.items():
                new_exp = _replace_values(exp, reports)
                report_calc = numexpr.evaluate(new_exp).astype(float)

                condition = condition + report_calc

                list_results.append(MathModelResult(value=condition, date=localtime(hour), mathmodel=math_model))
        MathModelResult.objects.bulk_create(list_results)


class MathModelListView(ListView):
    model = MathModel
    context_object_name = 'mathmodels'
    template_name = 'dashboard/mathmodel_update.html'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'mathmodel-update'  # Cria novo contexto

        return data


class CreateMathModel(CreateView, MathModelFormMixin):
    def form_valid(self, form):
        self.validate_form(form)

        return super().form_valid(form)


class UpdateMathModel(UpdateView, MathModelFormMixin):
    def get_initial(self):
        initial = super().get_initial()
        constants = Constant.objects.all().filter(mathmodel=self.object)
        string_all_constant = ''
        for constant in constants:
            string_const = f'{constant.name}={constant.value};'
            string_all_constant += string_const
        initial['constants'] = string_all_constant
        return initial

    def form_valid(self, form):
        self.validate_form(form)

        return super().form_valid(form)


class DeleteMathModel(DeleteView):
    model = MathModel
    template_name = 'dashboard/mathmodel_confirm_delete.html'
    success_url = reverse_lazy('dashboard:mathmodel_update')


class SensorListView(ListView):
    model = Sensor
    context_object_name = 'sensors'
    template_name = 'dashboard/sensor_update.html'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'sensor-update'  # Cria novo contexto

        return data


class SensorHumanListView(ListView):
    model = Sensor
    context_object_name = 'sensors'
    template_name = 'dashboard/sensor_human_update.html'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'sensor-human-update'  # Cria novo contexto

        return data

    def get_queryset(self):
        qs = Sensor.objects.all().filter(type__metric='bool')
        return qs


def create_sensor_human(request, pk):
    """Função que cria um novo sensor humano"""

    if request.method == "POST":
        updated_request = request.POST.copy()
        if updated_request['choice']:
            updated_request.update({'value': '1', 'sensor': pk})
        form = SensorHumanForm(updated_request)

        if form.is_valid():
            form.save()

            return redirect('dashboard:sensor_human_update')

    else:
        form = SensorHumanForm()

    context = {
        'form': form,
    }

    # Renderiza a página de criar sensor
    return render(request, 'dashboard/sensor_human_add.html', context)
