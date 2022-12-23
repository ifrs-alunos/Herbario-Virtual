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


class MathModelListView(ListView):
    model = MathModel
    context_object_name = 'mathmodels'
    template_name = 'dashboard/mathmodel_update.html'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data['link'] = 'mathmodel-update'  # Cria novo contexto

        return data


class CreateMathModel(CreateView):
    model = MathModel
    form_class = MathModelForm
    template_name = 'dashboard/mathmodel_create_form.html'
    success_url = reverse_lazy('dashboard:mathmodel_update')

    def form_valid(self, form):
        saved_form = form.save()
        constants = form.cleaned_data['constants'].split(";")
        for constant in constants:
            if constant != '':
                constant_string = constant.split("=")
                name = constant_string[0]
                value = constant_string[1]
                new_constant = Constant(name=name, value=value, mathmodel=saved_form)
                new_constant.save()

        exp = saved_form.source_code
        new_exp = ""
        for key, value in saved_form.constant_set.all().values_list('name', 'value'):
            exp = exp.replace(key, str(value))

        list_results = []
        for station in saved_form.stations.all():
            sensor_t = station.sensor_set.get(type__metric="C")
            sensor_rh = station.sensor_set.get(type__metric="%")
            reports_sensor_t = sensor_t.report_set.annotate(
                value_float=Cast('value', output_field=FloatField())) \
                .annotate(hour=TruncHour('time')) \
                .values('hour') \
                .annotate(avg_value=Avg('value_float')) \
                .order_by("hour")

            reports_sensor_rh = sensor_rh.report_set.annotate(
                value_float=Cast('value', output_field=FloatField())) \
                .annotate(hour=TruncHour('time')) \
                .values('hour') \
                .annotate(avg_value=Avg('value_float')) \
                .order_by("hour")
            zipped_models = zip(reports_sensor_t, reports_sensor_rh)
            condition = 0
            for temp, rh in zipped_models:
                hour = temp["hour"]
                new_exp = exp
                if float(rh['avg_value']) >= 85 and 10 < float(temp['avg_value']) < 26.5:
                    if "t" in exp:
                        new_exp = new_exp.replace('t', str(temp['avg_value']))
                    if "rh" in exp:
                        new_exp = new_exp.replace('rh', str(rh['avg_value']))
                    print(new_exp)
                    report_calc = numexpr.evaluate(new_exp).astype(float)
                    condition = condition + report_calc
                    print(report_calc,condition)
                else:
                    condition = 0

                list_results.append(MathModelResult(value=condition, date=localtime(hour), mathmodel=saved_form))

        MathModelResult.objects.bulk_create(list_results)

        return super().form_valid(form)


class UpdateMathModel(UpdateView):
    model = MathModel
    form_class = MathModelForm
    template_name = 'dashboard/mathmodel_create_form.html'
    success_url = reverse_lazy('dashboard:mathmodel_update')

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
        saved_form = form.save()
        saved_form.constant_set.all().delete()
        saved_form.mathmodelresult_set.all().delete()
        constants = form.cleaned_data['constants'].split(";")
        for constant in constants:
            if constant != '':
                constant_string = constant.split("=")
                name = constant_string[0]
                value = constant_string[1]
                new_constant = Constant(name=name, value=value, mathmodel=saved_form)
                new_constant.save()

        exp = saved_form.source_code
        new_exp = ""
        for key, value in saved_form.constant_set.all().values_list('name', 'value'):
            exp = exp.replace(key, str(value))
        list_results = []
        for station in saved_form.stations.all():
            sensor_t = station.sensor_set.get(type__metric="C")
            sensor_rh = station.sensor_set.get(type__metric="%")
            reports_sensor_t = sensor_t.report_set.annotate(
                value_float=Cast('value', output_field=FloatField())) \
                .annotate(hour=TruncHour('time')) \
                .values('hour') \
                .annotate(avg_value=Avg('value_float')) \
                .order_by("hour")

            reports_sensor_rh = sensor_rh.report_set.annotate(
                value_float=Cast('value', output_field=FloatField())) \
                .annotate(hour=TruncHour('time')) \
                .values('hour') \
                .annotate(avg_value=Avg('value_float')) \
                .order_by("hour")
            zipped_models = zip(reports_sensor_t, reports_sensor_rh)
            condition = 0
            for temp, rh in zipped_models:
                hour = temp["hour"]
                new_exp = exp
                if float(rh['avg_value']) >= 85 and 10 < float(temp['avg_value']) < 26.5:
                    if "t" in exp:
                        new_exp = new_exp.replace('t', str(temp['avg_value']))
                    if "rh" in exp:
                        new_exp = new_exp.replace('rh', str(rh['avg_value']))
                    report_calc = numexpr.evaluate(new_exp).astype(float)
                    condition = condition + report_calc
                else:
                    condition = 0

                list_results.append(MathModelResult(value=condition, date=localtime(hour), mathmodel=saved_form))
        MathModelResult.objects.bulk_create(list_results)

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
