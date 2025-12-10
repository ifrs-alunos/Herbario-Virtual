import numexpr
import logging
from django.db import models
from django.utils import timezone
from datetime import timedelta
from .base import BaseModel
import asyncio
from telegram_bot.models import TelegramUser
import requests

logger = logging.getLogger(__name__)

class MathModel(BaseModel):
    name = models.CharField("Nome do modelo matemático", max_length=100, blank=False)
    source_code = models.TextField(max_length=1000)
    disease = models.ForeignKey('disease.Disease', verbose_name="Doença", on_delete=models.PROTECT, null=True, blank=True)
    stations = models.ManyToManyField('alerts.Station', verbose_name="Estações associadas", blank=True)
    alert_threshold = models.FloatField("Limite para alertas", null=True, blank=True)
    alert_message = models.TextField("Mensagem de alerta", blank=True)
    evaluation_period = models.PositiveIntegerField("Período de avaliação (horas)", default=6)
    require_continuous_reports = models.BooleanField("Requisito de relatórios contínuos", default=True)
    min_positive_reports = models.PositiveIntegerField("Mínimo de relatórios positivos", default=3)
    is_active = models.BooleanField("Ativo", default=True)
    requirements = models.ManyToManyField('alerts.Requirement', through='MathModelRequirement', verbose_name="Requisitos", blank=True)
    min_conditions_hours = models.PositiveIntegerField("Horas mínimas de condições favoráveis", default=6)
    require_minimum_hours = models.BooleanField("Exigir horas mínimas", default=False)
    accumulation_start_hours = models.PositiveIntegerField("Horas para iniciar acumulação", default=0)
    retrospective_analysis_hours = models.PositiveIntegerField("Horas para análise retrospectiva", default=6)

    class Meta:
        verbose_name = "Modelo matemático"
        verbose_name_plural = "Modelos matemáticos"
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"

    def get_constants_dict(self):
        constants = self.constant_set.all()
        return {constant.name: constant.value for constant in constants}

    def evaluate_with_data(self, data: dict) -> float:
        if not data:
            return 0.0
        
        variables_dict = {
            't': data.get('t', 20) or 20,
            'rh': data.get('rh', 0) or 0,
            'rain': data.get('rain', 0) or 0,
        }
        
        constants_dict = self.get_constants_dict()
        local_dict = {**variables_dict, **constants_dict}
        
        required_constants = ['tbs', 'topt', 'tbi', 'rmax', 'c']
        for const in required_constants:
            if const not in constants_dict or constants_dict[const] is None:
                logger.warning(f"Constante {const} não encontrada no modelo {self.name}")
                return 0.0
        
        try:
            t = local_dict['t']
            tbs = local_dict['tbs']
            topt = local_dict['topt'] 
            tbi = local_dict['tbi']
            
            if (tbs - topt) == 0 or (topt - tbi) == 0:
                logger.warning(f"Divisão por zero evitada no modelo {self.name}")
                return 0.0
                
            base = ((t - tbi) / (topt - tbi))
            if base < 0:
                logger.warning(f"Base negativa para exponenciação no modelo {self.name}")
                return 0.0
            
            value = numexpr.evaluate(self.source_code, local_dict=local_dict)
            result = float(value)
            
            import math
            if math.isnan(result) or math.isinf(result):
                logger.warning(f"Resultado nan/inf gerado no modelo {self.name}")
                return 0.0
                
            return result
            
        except Exception as e:
            logger.error(f"Erro ao avaliar modelo {self.name}: {e}")
            return 0.0

    def _relatorio_tem_dados_minimos(self, report):
        """Verifica se o relatório tem dados mínimos usando APENAS sensores"""
        return report.has_minimum_data()

    def process_accumulation(self, station, report):
        from alerts.models.mathmodel_result import MathModelResult
        from alerts.models.tempo_de_analise import ConditionWindow
        
        try:
            print(f"🔍 Processando {self.name} para {station.alias} às {report.time}")
            
            if not self._relatorio_tem_dados_minimos(report):
                print("❌ Sem dados mínimos")
                return None
                
            if not self._verificar_requisitos_do_modelo_para_janela(report):
                print("❌ Não atende requisitos - RESETANDO")
                self._reset_accumulation_for_station(station)
                return None
            
            from django.utils import timezone
            import pytz
            
            tz_brasil = pytz.timezone('America/Sao_Paulo')
            current_time = timezone.now().astimezone(tz_brasil)
            
            print(f"🕒 TIMESTAMP BRASÍLIA: {current_time}")
            print(f"📍 Timezone: {current_time.tzinfo}")
            
            condition_window, created = ConditionWindow.objects.get_or_create(
                math_model=self,
                station=station,
                defaults={
                    'accumulation_start': current_time,
                    'last_valid_report': current_time,
                    'expected_alert_time': None,
                    'current_accumulated_value': 0.0,
                    'is_accumulation_active': False
                }
            )
            
            if not created and condition_window.accumulation_start and condition_window.accumulation_start.tzinfo is None:
                print(f"🔄 CORRIGINDO TIMEZONE da ConditionWindow existente")
                condition_window.accumulation_start = current_time
                condition_window.last_valid_report = current_time
                condition_window.save()
            
            current_data = report.get_sensor_data()
            current_value = self.evaluate_with_data(current_data)
            print(f"🧮 Valor calculado: {current_value:.3f}")
            
            if condition_window.is_accumulation_active:
                print("📈 Acumulação já está ativa")
                
                condition_window.current_accumulated_value += current_value
                condition_window.last_valid_report = current_time
                condition_window.save()
                
                print(f"➕ Acumulado: {condition_window.current_accumulated_value:.3f}")
                
                self._check_and_trigger_alert(condition_window, report.time)
                
            else:
                print("🚀 Iniciando nova acumulação")
                condition_window.accumulation_start = current_time
                condition_window.last_valid_report = current_time
                condition_window.current_accumulated_value = current_value
                condition_window.is_accumulation_active = True
                condition_window.expected_alert_time = None
                condition_window.save()
                
                print(f"🎯 Primeiro valor: {current_value:.3f}")
                print(f"🕒 Acumulação iniciada em: {current_time}")
                
                self._check_and_trigger_alert(condition_window, report.time)
            
            result = MathModelResult.objects.create(
                mathmodel=self,
                station=station,
                value=current_value,
                accumulated_value=condition_window.current_accumulated_value,
                date=report.time,
                is_alert_triggered=False
            )
            
            print(f"✅ Processamento concluído - Acumulado: {condition_window.current_accumulated_value:.3f}")
            return result

        except Exception as e:
            print(f"❌ Erro em process_accumulation: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    def _check_and_trigger_alert(self, condition_window, report_time):
        """Verifica e dispara alerta - COM TIMEZONE CORRETO"""
        from django.utils import timezone
        
        print(f"🔍 Verificando alerta para {condition_window.current_accumulated_value:.3f}")
        
        if condition_window.current_accumulated_value < self.alert_threshold:
            print(f"📊 Ainda não atingiu threshold: {condition_window.current_accumulated_value:.3f}/{self.alert_threshold}")
            return False
        
        print(f"✅ Threshold atingido: {condition_window.current_accumulated_value:.3f}/{self.alert_threshold}")
        
        if not self.require_minimum_hours or self.min_conditions_hours == 0:
            print("🚨 Disparando alerta IMEDIATO (sem horas mínimas)")
            self._trigger_alert_from_window(condition_window)
            return True

        current_time = timezone.localtime(timezone.now())
        
        if condition_window.expected_alert_time is not None:
            expected_local = timezone.localtime(condition_window.expected_alert_time)
            if current_time >= expected_local:
                print("🚨 DISPARANDO ALERTA AGENDADO - tempo mínimo atingido!")
                self._trigger_alert_from_window(condition_window)
                return True
            else:
                tempo_restante = expected_local - current_time
                print(f"⏳ Aguardando tempo mínimo: {tempo_restante}")
                return False
        
        alert_time = current_time + timedelta(hours=self.min_conditions_hours)
        condition_window.expected_alert_time = alert_time
        condition_window.save()
        
        print(f"⏰ Alerta AGENDADO para: {alert_time}")
        print(f"   Agora: {current_time}")
        print(f"   Horas requeridas: {self.min_conditions_hours}h")
        return False

    def _verificar_requisitos_do_modelo_para_janela(self, report):
        """Verifica se o relatório atende aos requisitos do modelo"""
        if not self.requirements.exists():
            return True
        
        print(f"🔍 Verificando {self.requirements.count()} requisitos")
        
        for requirement in self.requirements.all():
            if not requirement.is_active:
                continue
                
            atendido = requirement.validate_for_report(report)
            print(f"   {requirement.name}: {atendido}")
            
            if not atendido:
                print(f"❌ Requisito falhou: {requirement.name}")
                return False
        
        print("✅ Todos requisitos atendidos")
        return True

    def _extract_data_from_readings(self, report):
        """Método mantido para compatibilidade - usa get_sensor_data()"""
        return report.get_sensor_data()

    def _update_condition_hours(self, station, report):
        from alerts.models.tempo_de_analise import ConditionWindow
        
        try:
            condition_window, created = ConditionWindow.objects.get_or_create(
                math_model=self,
                station=station,
                defaults={
                    'window_start': report.time,
                    'conditions_met_minutes': 0.0,
                    'consecutive_positive_hours': 0.0,
                    'last_condition_time': report.time,
                    'is_minimum_met': False,
                    'first_positive_time': None,
                    'last_positive_time': None
                }
            )
            
            requirements_met = self._verificar_requisitos_do_modelo_para_janela(report)
            
            if created:
                print(f"🆕 ConditionWindow criado para {self.name} - {station.alias}")
                if requirements_met:
                    condition_window.conditions_met_minutes = 30.0
                    condition_window.consecutive_positive_hours = 0.5
                    condition_window.first_positive_time = report.time
                    condition_window.last_positive_time = report.time
                    condition_window.is_minimum_met = (30.0 >= self.min_conditions_hours * 60)
                    print(f"🆕 Primeiro relatório: +30min = {condition_window.conditions_met_minutes}min")
                condition_window.save()
                return condition_window
            
            MAX_GAP_MINUTES = 120
            MIN_INTERVAL_MINUTES = 10
            
            if requirements_met:
                time_diff_minutes = (report.time - condition_window.last_condition_time).total_seconds() / 60
                
                print(f"⏱️ Diferença desde último relatório: {time_diff_minutes:.1f} minutos")
                
                if time_diff_minutes <= MAX_GAP_MINUTES:
                    minutes_to_add = max(MIN_INTERVAL_MINUTES, time_diff_minutes)
                    condition_window.conditions_met_minutes += minutes_to_add
                    condition_window.consecutive_positive_hours = condition_window.conditions_met_minutes / 60
                    print(f"➕ Acumulando {minutes_to_add:.1f}min (gap: {time_diff_minutes:.1f}min)")
                else:
                    print(f"🔄 Nova acumulação - gap de {time_diff_minutes:.1f}min > {MAX_GAP_MINUTES}min")
                    condition_window.conditions_met_minutes = 30.0
                    condition_window.consecutive_positive_hours = 0.5
                    condition_window.window_start = report.time
                    condition_window.first_positive_time = report.time
                
                condition_window.last_condition_time = report.time
                condition_window.last_positive_time = report.time
                
                if condition_window.first_positive_time is None:
                    condition_window.first_positive_time = report.time
                
                condition_hours = condition_window.conditions_met_minutes / 60
                condition_window.is_minimum_met = (condition_hours >= self.min_conditions_hours)
                
                print(f"⏰ Acumulado: {condition_window.conditions_met_minutes:.1f}min ({condition_hours:.1f}h) de {self.min_conditions_hours}h - Mínimo: {condition_window.is_minimum_met}")
                
            else:
                if self.require_minimum_hours:
                    print("🔄 Condições não atendidas - resetando acumulação")
                    condition_window.conditions_met_minutes = 0
                    condition_window.consecutive_positive_hours = 0
                    condition_window.is_minimum_met = False
                    condition_window.first_positive_time = None
                else:
                    print("ℹ️ Condições não atendidas, mas horas mínimas não exigidas")
            
            condition_window.save()
            return condition_window
            
        except Exception as e:
            print(f"❌ Erro em _update_condition_hours: {e}")
            import traceback
            traceback.print_exc()
            return ConditionWindow(
                math_model=self,
                station=station,
                conditions_met_minutes=0,
                is_minimum_met=not self.require_minimum_hours
            )

    def _reset_condition_hours(self, station):
        from alerts.models.tempo_de_analise import ConditionWindow
        
        ConditionWindow.objects.filter(
            math_model=self,
            station=station
        ).update(
            conditions_met_minutes=0.0,
            consecutive_positive_hours=0.0,
            first_positive_time=None,
            last_positive_time=None,
            is_minimum_met=False,
            accumulation_reset=True
        )

    def trigger_alert(self, station, accumulated_value, current_data, condition_window=None):
        from alerts.models.alert_history import AlertHistory
        
        try:
            alerta_recente = AlertHistory.objects.filter(
                math_model=self,
                station=station,
                timestamp__gte=timezone.now() - timedelta(hours=6)
            ).exists()
            
            if alerta_recente:
                print("⏰ Alerta recente encontrado - evitando duplicação")
                return None
            
            disease_name = self.disease.name_disease if self.disease else "Doença"
            disease_description = getattr(self.disease, 'symptoms_disease', None) or "Condições favoráveis para desenvolvimento"
            
            format_data = {
                'value': accumulated_value, 
                'station': station.alias,
                'disease': disease_name,
                'temp': current_data.get('t', 0),
                't': current_data.get('t', 0),
                'rh': current_data.get('rh', 0), 
                'humidity': current_data.get('rh', 0),
                'rain': current_data.get('rain', 0),
                'model': self.name
            }
            
            if self.alert_message:
                try:
                    alert_message = self.alert_message.format(**format_data)
                except KeyError as e:
                    print(f"⚠️ Variável não encontrada na mensagem: {e}")
                    alert_message = f"Condições favoráveis para {disease_name}. Valor: {accumulated_value:.3f}"
            else:
                alert_message = f"Condições favoráveis para {disease_name}."
            
            alerta = AlertHistory.objects.create(
                math_model=self,
                station=station,
                details=f"Valor acumulado: {accumulated_value:.2f} | Modelo: {self.name}",
                calculated_value=accumulated_value,
                alert_message=alert_message
            )
            
            telegram_success = self._send_telegram_direct(station, accumulated_value, current_data, alert_message, condition_window, disease_name, disease_description)
            
            print(f"✅ Alerta criado: {disease_name} - {accumulated_value:.3f}")
            return alerta
                
        except Exception as e:
            print(f"Erro no trigger_alert: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _send_telegram_direct(self, station, accumulated_value, current_data, alert_message, condition_window=None, disease_name=None, disease_description=None):
        """Função para envio direto via Telegram"""
        try:
            from telegram_bot.models import TelegramUser
            from django.conf import settings
            import requests
            
            usuarios = TelegramUser.objects.filter(is_active=True)
            
            if not usuarios.exists():
                print("Nenhum usuário cadastrado no Telegram")
                return False
            
            print(f"Enviando para {usuarios.count()} usuários")
            
            temp = current_data.get('t', 0) or 0
            humidity = current_data.get('rh', 0) or 0
            
            full_message = (
                f"🚨 *ALERTA DE {disease_name.upper()}* 🚨\n\n"
                f"📍 *Estação:* {station.alias}\n"
                f"📊 *Modelo:* {self.name}\n"
                f"🌡️ *Temperatura:* {temp:.1f}°C\n"
                f"💧 *Umidade:* {humidity:.1f}%\n"
                f"\n💬 *Recomendação:*\n{alert_message}"
            )
            
            enviados = 0
            for usuario in usuarios:
                try:
                    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
                    payload = {
                        'chat_id': usuario.chat_id,
                        'text': full_message,
                        'parse_mode': 'Markdown'
                    }
                    
                    response = requests.post(url, json=payload, timeout=10)
                    
                    if response.status_code == 200:
                        enviados += 1
                        print(f"Alerta enviado para {usuario.first_name}")
                    else:
                        print(f"Erro API para {usuario.chat_id}: {response.status_code}")
                            
                except Exception as e:
                    print(f"Erro para {usuario.chat_id}: {e}")
            
            print(f"Alertas enviados: {enviados}/{usuarios.count()}")
            return enviados > 0
                
        except Exception as e:
            print(f"Erro no envio: {e}")
            return False

    def send_telegram_alert_directly(message):
        try:
            usuarios = TelegramUser.objects.filter(is_active=True)
            
            if not usuarios.exists():
                print("Nenhum usuário cadastrado no Telegram")
                return False
            
            print(f"Enviando para {usuarios.count()} usuários")
            
            enviados = 0
            for usuario in usuarios:
                try:
                    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
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

    def recalculate_all_windows(self, station=None):
        from alerts.models.tempo_de_analise import AnalysisWindow
        from alerts.models.report import Report

        windows = AnalysisWindow.objects.filter(math_model=self)
        if station:
            windows = windows.filter(station=station)

        recalculos = 0
        for window in windows:
            relatorios_na_janela = Report.objects.filter(
                station=window.station,
                time__gte=window.window_start,
                time__lt=window.window_end
            ).prefetch_related('readings__sensor__type')

            valid_reports = 0
            total_accumulated = 0.0

            for relatorio in relatorios_na_janela:
                if self._relatorio_tem_dados_minimos(relatorio) and self._verificar_requisitos_do_modelo_para_janela(relatorio):
                    valid_reports += 1
                    relatorio_data = self._extract_data_from_readings(relatorio)
                    valor_relatorio = self.evaluate_with_data(relatorio_data)
                    total_accumulated += valor_relatorio

            window.reports_in_window = relatorios_na_janela.count()
            window.valid_reports = valid_reports
            window.accumulated_value = total_accumulated
            window.is_complete = (valid_reports >= relatorios_na_janela.count() * 0.8)
            window.save()
            recalculos += 1

        return recalculos

    def check_and_send_pending_alerts(self, station=None):
        from alerts.models.mathmodel_result import MathModelResult
        from alerts.models.alert_history import AlertHistory
        
        resultados_sem_alerta = MathModelResult.objects.filter(mathmodel=self, is_alert_triggered=True)
        
        if station:
            resultados_sem_alerta = resultados_sem_alerta.filter(station=station)
        
        alert_count = 0
        for resultado in resultados_sem_alerta:
            alerta_existente = AlertHistory.objects.filter(
                math_model=self,
                station=resultado.station,
                calculated_value=resultado.accumulated_value,
                timestamp__date=resultado.date.date()
            ).exists()
            
            if not alerta_existente:
                current_data = {'t': resultado.value or 0, 'rh': 0, 'rain': 0}
                self.trigger_alert(resultado.station, resultado.accumulated_value, current_data)
                alert_count += 1
        
        return alert_count
    
    def analyze_retrospective_alert(self, station, current_report):
        from alerts.models.mathmodel_result import MathModelResult
        from alerts.models.tempo_de_analise import ConditionWindow
        from django.utils import timezone
        from datetime import timedelta
        
        try:
            condition_window, created = ConditionWindow.objects.get_or_create(
                math_model=self,
                station=station,
                defaults={
                    'window_start': current_report.time,
                    'conditions_met_minutes': 0.0,
                    'consecutive_positive_hours': 0.0,
                    'last_condition_time': current_report.time,
                    'is_minimum_met': False
                }
            )
            
            condition_window = self._update_condition_hours(station, current_report)
            
            consecutive_hours = condition_window.consecutive_positive_hours
            has_minimum_hours = consecutive_hours >= self.min_conditions_hours
            
            if not has_minimum_hours and self.require_minimum_hours:
                return False, 0.0, f"Horas insuficientes: {consecutive_hours:.2f}h"

            current_time = current_report.time
            analysis_start = current_time - timedelta(hours=self.retrospective_analysis_hours)
            
            all_results = MathModelResult.objects.filter(
                mathmodel=self,
                station=station,
                date__gte=analysis_start,
                date__lte=current_time
            ).order_by('date')
            
            if all_results.count() == 0:
                return False, 0.0, "Nenhum dado"
            
            current_accumulated = all_results.last().accumulated_value
            
            should_alert = (current_accumulated >= self.alert_threshold)
            if self.require_minimum_hours:
                should_alert = should_alert and has_minimum_hours
            
            history = f"Acumulado:{current_accumulated:.3f}|Horas:{consecutive_hours:.2f}/{self.min_conditions_hours}|Alerta:{should_alert}"
            
            return should_alert, current_accumulated, history
            
        except Exception as e:
            return False, 0.0, f"Erro: {e}"
        
    def _reset_accumulation_for_station(self, station):
        """Reseta acumulação para uma estação específica"""
        from alerts.models.tempo_de_analise import ConditionWindow
        
        try:
            condition_windows = ConditionWindow.objects.filter(
                math_model=self,
                station=station
            )
            
            for window in condition_windows:
                window.accumulation_start = None
                window.last_valid_report = None
                window.expected_alert_time = None
                window.current_accumulated_value = 0.0
                window.is_accumulation_active = False
                window.save()
            
            print(f"🔄 Acumulação resetada para {station.alias}")
            
        except Exception as e:
            print(f"❌ Erro ao resetar acumulação: {e}")

    def _schedule_alert(self, condition_window, report_time):
        """Agenda um alerta para daqui a X horas - CORREÇÃO TIMEZONE"""
        from django.utils import timezone
        from datetime import timedelta

        if not self.require_minimum_hours or self.min_conditions_hours == 0:
            print("🚨 Disparando alerta imediato (sem horas mínimas)")
            self._trigger_alert_from_window(condition_window)
            return

        if condition_window.expected_alert_time is not None:
            print(f"⏰ Alerta já agendado para: {condition_window.expected_alert_time}")
            return

        alert_time = timezone.now() + timedelta(hours=self.min_conditions_hours)

        condition_window.expected_alert_time = alert_time
        condition_window.save()

        print(f"⏰ Alerta agendado para: {alert_time}")
        print(f"   Agora: {timezone.now()}")
        print(f"   Duração requerida: {self.min_conditions_hours}h")

    def _reset_accumulation(self, condition_window):
        """Reseta completamente a acumulação"""
        condition_window.accumulation_start = None
        condition_window.last_valid_report = None
        condition_window.expected_alert_time = None
        condition_window.current_accumulated_value = 0.0
        condition_window.is_accumulation_active = False
        condition_window.save()
        print("🔄 Acumulação resetada")

    def _check_pending_alerts(self, station):
        """Verifica e dispara alertas pendentes para esta estação"""
        from alerts.models.tempo_de_analise import ConditionWindow
        
        try:
            current_time = timezone.now()
            print(f"🔍 Verificando alertas pendentes para {self.name} - {station.alias}")
            
            pending_windows = ConditionWindow.objects.filter(
                math_model=self,
                station=station,
                is_accumulation_active=True,
                expected_alert_time__isnull=False
            )
            
            print(f"📋 Alertas pendentes encontrados: {pending_windows.count()}")
            
            for window in pending_windows:
                print(f"🔎 Analisando: Agendado para {window.expected_alert_time}")
                print(f"   ⏰ Já passou? {current_time >= window.expected_alert_time}")
                print(f"   📈 Acumulado: {window.current_accumulated_value}")
                print(f"   🎯 Threshold: {self.alert_threshold}")
                
                if (current_time >= window.expected_alert_time and 
                    window.current_accumulated_value >= self.alert_threshold):
                    print(f"🚨 DISPARANDO ALERTA AGENDADO!")
                    self._trigger_alert_from_window(window)
                else:
                    print(f"⏳ Ainda não é hora")
                    
        except Exception as e:
            print(f"❌ Erro ao verificar alertas pendentes: {e}")

    def _trigger_alert_from_window(self, condition_window):
        """Dispara alerta a partir de um ConditionWindow"""
        try:
            from alerts.models.report import Report
            last_report = Report.objects.filter(
                station=condition_window.station,
                time=condition_window.last_valid_report
            ).first()

            current_data = {}
            if last_report:
                current_data = last_report.get_sensor_data()
            else:
                current_data = {'t': 0, 'rh': 0, 'rain': 0}

            alerta = self.trigger_alert(
                condition_window.station,
                condition_window.current_accumulated_value,
                current_data,
                condition_window
            )

            # Reset accumulation after alert is triggered
            if alerta:
                print("🔄 Resetando acumulação após alerta disparado")
                self._reset_accumulation(condition_window)

        except Exception as e:
            print(f"❌ Erro ao disparar alerta: {e}")
