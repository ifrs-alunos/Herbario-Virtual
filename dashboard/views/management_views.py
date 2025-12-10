from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from alerts.models import Station, Constant, Requirement, AlertHistory
from dashboard.forms.management_forms import StationForm, ConstantForm, RequirementForm
from django.conf import settings

class StationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Station
    template_name = 'dashboard/station_list.html'
    permission_required = 'alerts.view_station'
    context_object_name = 'station_list'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'station_list'
        return context

class StationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Station
    form_class = StationForm
    template_name = 'dashboard/station_form.html'
    success_url = reverse_lazy('dashboard:station_list')
    permission_required = 'alerts.add_station'

    def form_valid(self, form):
        messages.success(self.request, "Estação criada com sucesso!")
        return super().form_valid(form)

class StationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Station
    form_class = StationForm
    template_name = 'dashboard/station_form.html'
    success_url = reverse_lazy('dashboard:station_list')
    permission_required = 'alerts.change_station'

    def form_valid(self, form):
        messages.success(self.request, "Estação atualizada com sucesso!")
        return super().form_valid(form)

class StationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Station
    template_name = 'dashboard/station_confirm_delete.html'
    success_url = reverse_lazy('dashboard:station_list')
    permission_required = 'alerts.delete_station'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Estação excluída com sucesso!")
        return super().delete(request, *args, **kwargs)

class ConstantListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Constant
    template_name = 'dashboard/constant_list.html'
    permission_required = 'alerts.view_constant'
    context_object_name = 'constant_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'constant_list'
        return context

class ConstantCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Constant
    form_class = ConstantForm
    template_name = 'dashboard/constant_form.html'
    success_url = reverse_lazy('dashboard:constant_list')
    permission_required = 'alerts.add_constant'

    def form_valid(self, form):
        messages.success(self.request, "Constante criada com sucesso!")
        return super().form_valid(form)

class ConstantUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Constant
    form_class = ConstantForm
    template_name = 'dashboard/constant_form.html'
    success_url = reverse_lazy('dashboard:constant_list')
    permission_required = 'alerts.change_constant'

    def form_valid(self, form):
        messages.success(self.request, "Constante atualizada com sucesso!")
        return super().form_valid(form)

class ConstantDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Constant
    template_name = 'dashboard/constant_confirm_delete.html'
    success_url = reverse_lazy('dashboard:constant_list')
    permission_required = 'alerts.delete_constant'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Constante excluída com sucesso!")
        return super().delete(request, *args, **kwargs)

class RequirementListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Requirement
    template_name = 'dashboard/requirement_list.html'
    permission_required = 'alerts.view_requirement'
    context_object_name = 'requirement_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'requirement_list'
        return context

class RequirementCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Requirement
    form_class = RequirementForm
    template_name = 'dashboard/requirement_form.html'
    success_url = reverse_lazy('dashboard:requirement_list')
    permission_required = 'alerts.add_requirement'

    def form_valid(self, form):
        messages.success(self.request, "Requisito criado com sucesso!")
        return super().form_valid(form)

class RequirementUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Requirement
    form_class = RequirementForm
    template_name = 'dashboard/requirement_form.html'
    success_url = reverse_lazy('dashboard:requirement_list')
    permission_required = 'alerts.change_requirement'

    def form_valid(self, form):
        messages.success(self.request, "Requisito atualizado com sucesso!")
        return super().form_valid(form)

class RequirementDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Requirement
    template_name = 'dashboard/requirement_confirm_delete.html'
    success_url = reverse_lazy('dashboard:requirement_list')
    permission_required = 'alerts.delete_requirement'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Requisito excluído com sucesso!")
        return super().delete(request, *args, **kwargs)

class AlertHistoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = AlertHistory
    template_name = 'dashboard/alert_history.html'
    permission_required = 'alerts.view_alerthistory'
    context_object_name = 'alert_history_list'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'alert_history'
        return context

class TelegramSubscriptionView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/telegram_subscription.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'telegram-subscription'
        context['bot_username'] = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'labfito_alertas_bot')
        context['user_subscriptions'] = []
        return context

class ManualAlertView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'dashboard/manual_alert.html'
    permission_required = 'alerts.add_alerthistory'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'manual_alert'
        from alerts.models import MathModel, Station
        context['math_models'] = MathModel.objects.filter(is_active=True)
        context['stations'] = Station.objects.all()
        return context
    
    def post(self, request, *args, **kwargs):
        math_model_id = request.POST.get('math_model')
        station_id = request.POST.get('station')
        message = request.POST.get('message')
        value = request.POST.get('value', 0)
        temperature = request.POST.get('temperature', '')
        humidity = request.POST.get('humidity', '')
        
        try:
            from alerts.models import MathModel, Station, AlertHistory
            from django.utils import timezone
            
            math_model = MathModel.objects.get(id=math_model_id)
            station = Station.objects.get(id=station_id)
            
            disease_name = math_model.disease.name_disease if math_model.disease else "Doença"
            
            format_data = {
                'value': float(value),
                'station': station.alias,
                'disease': disease_name,
                'temp': temperature if temperature else 'N/A',
                't': temperature if temperature else 'N/A',
                'humidity': humidity if humidity else 'N/A',
                'rh': humidity if humidity else 'N/A',
                'rain': '0',
                'model': math_model.name
            }
            
            try:
                formatted_message = message.format(**format_data)
            except KeyError as e:
                formatted_message = message
                messages.warning(request, f"Variável {e} não encontrada - usando mensagem sem formatação")
            except Exception as e:
                formatted_message = message
                print(f"Erro na formatação: {e}")
            
            alert = AlertHistory.objects.create(
                math_model=math_model,
                station=station,
                alert_time=timezone.now(),
                alert_value=float(value),
                alert_message=formatted_message,
                details=f"Alerta manual - Valor: {value} | Temp: {temperature}°C | Umidade: {humidity}%",
                calculated_value=float(value)
            )
            
            telegram_success = self.send_telegram_alert_directly(formatted_message)
            
            if telegram_success:
                messages.success(request, "Alerta manual enviado com sucesso!")
            else:
                messages.warning(request, "Alerta criado, mas houve problemas no envio do Telegram.")
            
        except Exception as e:
            messages.error(request, f"Erro ao enviar alerta: {str(e)}")
        
        return redirect('dashboard:manual_alert')

    def send_telegram_alert_directly(self, message):
        try:
            from telegram_bot.models import TelegramUser
            from django.conf import settings
            import requests
            
            usuarios = TelegramUser.objects.filter(is_active=True)
            
            if not usuarios.exists():
                print("Nenhum usuário cadastrado no Telegram")
                return False
            
            print(f"Enviando para {usuarios.count()} usuários")
            
            enviados = 0
            for usuario in usuarios:
                try:
                    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
                    payload = {
                        'chat_id': usuario.chat_id,
                        'text': message,
                        'parse_mode': 'Markdown'
                    }
                    
                    print(f"Enviando para chat_id: {usuario.chat_id}")
                    response = requests.post(url, json=payload, timeout=10)
                    
                    if response.status_code == 200:
                        enviados += 1
                        print(f"Mensagem enviada para {usuario.first_name}")
                    else:
                        print(f"Erro API Telegram: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    print(f"Erro no envio para {usuario.chat_id}: {e}")
            
            print(f"Total enviados: {enviados}/{usuarios.count()}")
            return enviados > 0
            
        except Exception as e:
            print(f"Erro geral no envio Telegram: {e}")
            return False