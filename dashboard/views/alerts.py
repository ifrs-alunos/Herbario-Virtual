import re
import numexpr
from django.db.models import Avg
from django.db.models.functions import TruncHour
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.timezone import localtime, now
from django.views.generic import CreateView, UpdateView, ListView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.db import transaction
import logging
from ..forms import MathModelForm
from ..forms.sensor_human_form import SensorHumanForm
from alerts.models import MathModel, Sensor, Constant, MathModelResult
from django.views.generic import TemplateView
from alerts.models import Station

logger = logging.getLogger(__name__)

def _create_constants(constants_string: str, saved_form) -> None:
    """Cria constantes a partir de uma string formatada"""
    if not constants_string:
        return
        
    constants = constants_string.split(";")
    for constant in constants:
        if constant.strip():
            try:
                name, value = constant.split("=")
                new_constant = Constant(name=name.strip(), value=value.strip(), mathmodel=saved_form)
                new_constant.save()
            except ValueError:
                continue


def _replace_values(exp: str, values_dict: dict) -> str:
    """Substitui variáveis na expressão por seus valores"""
    tokens = re.split(r'(\W+)', exp)
    new_tokens = [values_dict.get(token, token) for token in tokens]
    return "".join(new_tokens)


class MathModelFormMixin:
    """Mixin para validação de formulários de modelos matemáticos"""
    
    def validate_form(self, form: MathModelForm) -> None:
        """Valida e processa o formulário do modelo matemático - VERSÃO OTIMIZADA"""
        try:
            with transaction.atomic():
                math_model: MathModel = form.save(commit=False)
                math_model.save()
                
                math_model.constant_set.all().delete()
                
                _create_constants(form.cleaned_data.get('constants', ''), math_model)

                constants_dict = {
                    name: str(value) 
                    for name, value in math_model.constant_set.values_list('name', 'value')
                }

                exp = _replace_values(math_model.source_code, constants_dict)
                
                MathModelResult.objects.filter(mathmodel=math_model).delete()
                
                form.save_m2m()
                
                self._process_recent_data(math_model, exp)
                
        except Exception as e:
            logger.error(f"Erro ao validar formulário: {e}")
            raise

    def _process_recent_data(self, math_model, exp):
        """Processa apenas dados recentes para evitar lentidão"""
        from django.utils.timezone import timedelta
        
        time_threshold = now() - timedelta(days=30)
        list_results = []

        for station in math_model.stations.all():
            station_results = self._process_station_data(station, exp, time_threshold, math_model)
            list_results.extend(station_results)
        
        if list_results:
            MathModelResult.objects.bulk_create(list_results, batch_size=100)

    def _process_station_data(self, station, exp, time_threshold, math_model):
        """Processa dados de uma estação específica"""
        results = []
        reports_by_hour = {}

        relevant_sensors = station.sensor_set.filter(
            type__name__in=['temperature', 'humidity', 'rain']
        )

        for sensor in relevant_sensors:
            name = sensor.type.name

            reports = sensor.reading_set.filter(
                time__gte=time_threshold
            ).annotate(
                hour=TruncHour('time', is_dst=False)
            ).values(
                'hour'
            ).annotate(
                avg_value=Avg('value')
            ).order_by("hour")

            for report in reports:
                hour = report['hour']
                if hour not in reports_by_hour:
                    reports_by_hour[hour] = {}
                reports_by_hour[hour][name] = report['avg_value']

        for hour, reports in reports_by_hour.items():
            reports.setdefault('temperature', 0)
            reports.setdefault('humidity', 0)
            reports.setdefault('rain', 0)
            
            try:
                new_exp = _replace_values(exp, reports)
                result_value = float(numexpr.evaluate(new_exp))
                
                results.append(MathModelResult(
                    value=result_value, 
                    date=localtime(hour), 
                    mathmodel=math_model,
                    station=station
                ))
            except Exception as e:
                print(f"Erro ao calcular expressão para hora {hour}: {e}")
                continue
        
        return results

class SensorListView(LoginRequiredMixin, ListView):
    model = Sensor
    context_object_name = 'sensors'
    template_name = 'dashboard/sensor_list.html'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['link'] = 'sensor-list'
        return data

class SensorHumanListView(LoginRequiredMixin, ListView):
    model = Sensor
    context_object_name = 'sensors'
    template_name = 'dashboard/sensor_human_update.html'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['link'] = 'sensor-human-update'
        return data

    def get_queryset(self):
        return Sensor.objects.filter(type__metric='human')

def create_sensor_human(request, pk):
    """Função que cria um novo sensor humano"""
    if request.method == "POST":
        updated_request = request.POST.copy()
        if updated_request.get('choice'):
            updated_request.update({'value': '1', 'sensor': pk})
        form = SensorHumanForm(updated_request)

        if form.is_valid():
            form.save()
            messages.success(request, "Sensor humano criado com sucesso!")
            return redirect('dashboard:sensor_human_update')
    else:
        form = SensorHumanForm()

    context = {
        'form': form,
    }

    return render(request, 'dashboard/sensor_human_add.html', context)

class MathModelListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = MathModel
    context_object_name = 'mathmodels'
    template_name = 'dashboard/mathmodel_update.html'
    paginate_by = 12
    permission_required = 'alerts.view_mathmodel'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['link'] = 'mathmodel-update'
        return data

class CreateMathModel(LoginRequiredMixin, PermissionRequiredMixin, CreateView, MathModelFormMixin):
    model = MathModel
    form_class = MathModelForm
    template_name = 'dashboard/mathmodel_create_form.html'
    success_url = reverse_lazy('dashboard:mathmodel_update')
    permission_required = 'alerts.add_mathmodel'

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            self.validate_form(form)
            messages.success(self.request, "Modelo matemático criado com sucesso!")
            return response
        except Exception as e:
            messages.error(self.request, f"Erro ao criar modelo: {e}")
            return self.form_invalid(form)


class UpdateMathModel(LoginRequiredMixin, PermissionRequiredMixin, UpdateView, MathModelFormMixin):
    model = MathModel
    form_class = MathModelForm
    template_name = 'dashboard/mathmodel_create_form.html'
    success_url = reverse_lazy('dashboard:mathmodel_update')
    permission_required = 'alerts.change_mathmodel'

    def get_queryset(self):
        return MathModel.objects.all()

    def get_initial(self):
        initial = super().get_initial()
        constants = Constant.objects.filter(mathmodel=self.object)
        string_all_constant = ';'.join([f'{constant.name}={constant.value}' for constant in constants])
        initial['constants'] = string_all_constant
        return initial

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            self.validate_form(form)
            messages.success(self.request, "Modelo matemático atualizado com sucesso!")
            return response
        except Exception as e:
            messages.error(self.request, f"Erro ao atualizar modelo: {e}")
            return self.form_invalid(form)


class DeleteMathModel(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = MathModel
    template_name = 'dashboard/mathmodel_confirm_delete.html'
    success_url = reverse_lazy('dashboard:mathmodel_update')
    permission_required = 'alerts.delete_mathmodel'

    def get_queryset(self):
        return MathModel.objects.all()
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        try:
            with transaction.atomic():
                MathModelResult.objects.filter(mathmodel=self.object).delete()
                Constant.objects.filter(mathmodel=self.object).delete()
                
                self.object.stations.clear()
                self.object.requirements.clear()
                
                self.object.delete()
                
                messages.success(self.request, "Modelo matemático excluído com sucesso!")
                return redirect(self.get_success_url())
                
        except Exception as e:
            logger.error(f"Erro ao excluir modelo matemático: {e}")
            messages.error(self.request, f"Erro ao excluir modelo: {e}")
            return redirect(self.get_success_url())
    
class MathModelResultsView(LoginRequiredMixin, ListView):
    """View para ver todos os resultados de um modelo matemático"""
    model = MathModelResult
    template_name = 'dashboard/mathmodel_results.html'
    context_object_name = 'results'
    
    def get_queryset(self):
        mathmodel_id = self.kwargs.get('mathmodel_id')
        station_id = self.kwargs.get('station_id')
        
        queryset = MathModelResult.objects.all()
        
        if mathmodel_id:
            queryset = queryset.filter(mathmodel_id=mathmodel_id)
        if station_id:
            queryset = queryset.filter(station_id=station_id)
            
        return queryset.order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mathmodel'] = MathModel.objects.get(id=self.kwargs.get('mathmodel_id'))
        context['station'] = Station.objects.get(id=self.kwargs.get('station_id'))
        return context
    