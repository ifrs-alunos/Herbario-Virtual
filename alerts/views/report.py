import json
import logging
from datetime import datetime
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

logger = logging.getLogger('django')

@method_decorator(csrf_exempt, name="dispatch")
class ReportView(View):
    """Processa relatórios das estações e dispara alertas - VERSÃO CORRIGIDA"""
    
    def post(self, request):
        try:
            dados = json.loads(request.body.decode("utf-8"))
            logger.info(f"📥 Dados recebidos: {dados}")

            estacao = self._obter_estacao(dados.get("chipid"))
            relatorio = self._criar_relatorio(estacao, dados)
            self._processar_leituras(dados.get("readings", []), relatorio)
            
            self._processar_modelos_matematicos(relatorio)
            
            return JsonResponse({"status": "sucesso", "relatorio_id": relatorio.id}, status=200)

        except Exception as e:
            logger.error(f"❌ Erro inesperado: {str(e)}")
            return JsonResponse({"erro": "Falha no processamento"}, status=500)

    def _obter_estacao(self, chipid):
        from alerts.models import Station
        if not chipid:
            raise ValueError("ID do chip não fornecido")
        try:
            return Station.objects.get(station_id=chipid)
        except Station.DoesNotExist:
            logger.error(f"❌ Estação com chipid {chipid} não encontrada")
            raise ValueError(f"Estação {chipid} não encontrada")

    def _criar_relatorio(self, estacao, dados):
        from alerts.models import Report
        try:
            relatorio = Report(station=estacao)
            
            if dados.get("time"):
                try:
                    relatorio.time = datetime.fromisoformat(dados.get("time").replace('Z', '+00:00'))
                except ValueError:
                    logger.warning("⚠️ Formato de data inválido, usando data atual")
                    relatorio.time = datetime.now()
            else:
                relatorio.time = datetime.now()
                
            relatorio.save()
            logger.info(f"✅ Relatório criado: ID {relatorio.id}")
            return relatorio
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar relatório: {e}")
            raise

    def _processar_leituras(self, leituras, relatorio):
        from alerts.models import Reading, TypeSensor
        sensores_processados = []
        
        logger.info(f"🔍 Processando {len(leituras)} leituras")
        
        for leitura in leituras:
            try:
                sensor_name = leitura.get("sensor_name")
                sensor_value = leitura.get("value")
                
                if not sensor_name or sensor_value is None:
                    logger.warning(f"⚠️ Leitura inválida: {leitura}")
                    continue

                try:
                    tipo_sensor = TypeSensor.objects.get(name=sensor_name)
                    sensor = relatorio.station.sensor_set.get(type=tipo_sensor)
                except (TypeSensor.DoesNotExist, Exception):
                    logger.warning(f"⚠️ Sensor {sensor_name} não encontrado, criando...")
                    tipo_sensor, created = TypeSensor.objects.get_or_create(
                        name=sensor_name,
                        defaults={'metric': 'C' if 'temp' in sensor_name.lower() else 
                                 '%' if 'hum' in sensor_name.lower() else 'mm'}
                    )
                    sensor, created = relatorio.station.sensor_set.get_or_create(
                        type=tipo_sensor,
                        defaults={'name': f"{relatorio.station.alias} - {sensor_name}"}
                    )

                reading = Reading.objects.create(
                    sensor=sensor,
                    value=float(sensor_value),
                    report=relatorio,
                    time=relatorio.time
                )
                
                sensores_processados.append(sensor)
                logger.info(f"✅ Leitura processada: {sensor_name} = {sensor_value}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar leitura {leitura}: {str(e)}")
                
        return sensores_processados

    def _processar_modelos_matematicos(self, relatorio):
        """Processa modelos matemáticos para o relatório - VERSÃO CORRIGIDA"""
        try:
            from alerts.models import MathModel

            logger.info(f"🔍 Processando modelos matemáticos para relatório {relatorio.id}")

            math_models = MathModel.objects.filter(
                stations=relatorio.station,
                is_active=True
            )

            logger.info(f"🔍 Encontrados {math_models.count()} modelos ativos")

            alerta_disparado = False

            for math_model in math_models:
                logger.info(f"🔍 Verificando modelo: {math_model.name}")

                requisitos_atendidos = self._verificar_requisitos(math_model, relatorio)
                logger.info(f"🔍 Requisitos atendidos para {math_model.name}: {requisitos_atendidos}")

                if requisitos_atendidos:
                    logger.info(f"✅✅✅ PROCESSANDO MODELO {math_model.name}")

                    resultado = math_model.process_accumulation(relatorio.station, relatorio)

                    if resultado and resultado.is_alert_triggered:
                        logger.info(f"🚨🚨🚨 ALERTA DISPARADO por {math_model.name}!")
                        self._disparar_alertas(math_model, relatorio.station, resultado)
                        alerta_disparado = True
                    else:
                        logger.info(f"ℹ️ Modelo {math_model.name} processado sem alerta")
                else:
                    logger.info(f"❌ Modelo {math_model.name} não atende aos requisitos")

            # Atualizar risk_alert do relatório se algum alerta foi disparado
            if alerta_disparado and not relatorio.risk_alert:
                relatorio.risk_alert = True
                relatorio.save(update_fields=['risk_alert'])
                logger.info(f"✅ Risk alert atualizado para relatório {relatorio.id}")

        except Exception as e:
            logger.error(f"❌ Erro ao processar modelos matemáticos: {e}")

    def _verificar_requisitos(self, math_model, relatorio):
        """Verifica se o relatório atende aos requisitos do modelo"""
        try:
            if not math_model.requirements.exists():
                return True
            
            for requirement in math_model.requirements.all():
                if not requirement.is_active:
                    continue
                    
                atendido = requirement.validate_for_report(relatorio)
                logger.info(f"🔍 Requisito {requirement.name}: {atendido}")
                
                if not atendido:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar requisitos: {e}")
            return False

    def _disparar_alertas(self, modelo_matematico, estacao, resultado):
        """Dispara alertas quando um modelo detecta risco"""
        try:
            logger.info(f"📤 Disparando alertas para {modelo_matematico.name}")
            
            self._disparar_alertas_whatsapp(modelo_matematico, estacao, resultado)
            
            self._disparar_alertas_telegram(modelo_matematico, estacao, resultado)
            
        except Exception as e:
            logger.error(f"❌ Erro ao disparar alertas: {e}")

    def _disparar_alertas_whatsapp(self, modelo_matematico, estacao, resultado):
        """Dispara alertas via WhatsApp"""
        try:
            from accounts.models import Profile
            from whatsapp_messages.services import enviar_alerta_whatsapp
            
            perfis = Profile.objects.filter(
                alerts_for_diseases=modelo_matematico.disease,
                whatsapp_opt_in=True,
                whatsapp_verified=True
            )
            
            for perfil in perfis:
                try:
                    mensagem = (
                        f"🚨 ALERTA: {modelo_matematico.disease.name_disease}\n"
                        f"📍 Estação: {estacao.alias or estacao.station_id}\n"
                        f"📊 Nível de Risco: {resultado.accumulated_value:.2f}\n"
                        f"⏰ Horário: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                    )
                    enviar_alerta_whatsapp(perfil.phone, mensagem)
                    logger.info(f"✅ Alerta WhatsApp enviado para {perfil.phone}")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao enviar alerta WhatsApp para {perfil.phone}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Erro geral nos alertas WhatsApp: {e}")

    def _disparar_alertas_telegram(self, modelo_matematico, estacao, resultado):
        """Dispara alertas via Telegram"""
        try:
            from telegram_bot.handlers import bot_instance
            
            if not bot_instance:
                logger.warning("⚠️ Bot do Telegram não disponível")
                return
            
            alerta_telegram = (
                f"⚠️ *ALERTA: {modelo_matematico.disease.name_disease.upper()}*\n"
                f"🏢 *Estação:* {estacao.alias or estacao.station_id}\n"
                f"🔢 *Nível de risco:* {resultado.accumulated_value:.2f}\n"
                f"📈 *Limite:* {modelo_matematico.alert_threshold}\n"
                f"⏰ *Horário:* {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )

            if hasattr(bot_instance, 'enviar_alerta_para_todos_sincrono'):
                bot_instance.enviar_alerta_para_todos_sincrono(alerta_telegram)
            else:
                logger.warning("⚠️ Método de envio síncrono não disponível")
                
        except Exception as e:
            logger.error(f"❌ Erro nos alertas Telegram: {e}")

class LastReport(View):
    """Obtém o último relatório de uma estação"""
    
    def get(self, request, station_chip_id):
        try:
            from alerts.models import Station, Report
            
            estacao = Station.objects.get(station_id=station_chip_id)
            ultimo_relatorio = Report.objects.filter(station=estacao).order_by("-time").first()
            
            if not ultimo_relatorio:
                return JsonResponse({"erro": "Nenhum relatório encontrado"}, status=404)
                
            return JsonResponse({
                "hora": ultimo_relatorio.time.isoformat() if ultimo_relatorio.time else None,
                "estacao": estacao.alias,
                "temperatura": ultimo_relatorio.temperatura,
                "umidade": ultimo_relatorio.umidade,
                "tempo_chuva": ultimo_relatorio.tempo_chuva,
                "risk_alert": ultimo_relatorio.risk_alert
            })
            
        except Station.DoesNotExist:
            return JsonResponse({"erro": "Estação não encontrada"}, status=404)
        except Exception as e:
            return JsonResponse({"erro": str(e)}, status=400)