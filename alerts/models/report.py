from django.db import models
from django.utils import timezone
import logging
from datetime import timedelta
from .base import BaseModel

logger = logging.getLogger(__name__)

class Report(BaseModel):
    station = models.ForeignKey('Station', on_delete=models.CASCADE)
    time = models.DateTimeField(default=timezone.now)
    temperatura = models.FloatField(null=True, blank=True)
    umidade = models.FloatField(null=True, blank=True)
    tempo_chuva = models.FloatField(null=True, blank=True)
    risk_alert = models.BooleanField(default=False)
    reading_temp = models.FloatField(null=True, blank=True, verbose_name="Leitura Temperatura")
    reading_humidity = models.FloatField(null=True, blank=True, verbose_name="Leitura Umidade")
    reading_rain = models.FloatField(null=True, blank=True, verbose_name="Leitura Chuva")
    processed = models.BooleanField(default=False, verbose_name="Processado")
    processing = models.BooleanField(default=False, verbose_name="Em processamento")

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new:
            print(f"📋 Relatório {self.id} criado - AGUARDANDO READINGS VIA SIGNAL")

    def get_sensor_data(self):
        """Extrai dados APENAS dos sensores - FONTE PRINCIPAL"""
        sensor_data = {
            't': None,  # temperatura
            'rh': None, # umidade
            'rain': None # chuva
        }
        
        if hasattr(self, 'readings') and self.readings.exists():
            for reading in self.readings.all():
                sensor_metric = reading.sensor.type.metric.lower()
                value = reading.value
                
                if value is not None:
                    if sensor_metric in ['dht_t', 'bmp_t', 'c', 'cs', 'k']:
                        sensor_data['t'] = float(value)
                    elif sensor_metric in ['dht_h', '%', 'ur', 'pct']:
                        sensor_data['rh'] = float(value)
                    elif sensor_metric in ['rain', 'mm']:
                        sensor_data['rain'] = float(value)
        
        #print(f"📊 Dados extraídos dos sensores: {sensor_data}")
        return sensor_data

    def has_minimum_data(self):
        """Verifica se tem pelo menos temperatura e umidade dos SENSORES"""
        data = self.get_sensor_data()
        has_data = data['t'] is not None and data['rh'] is not None
        print(f"🔍 Dados mínimos dos sensores: {has_data} (t: {data['t']}, rh: {data['rh']})")
        return has_data

    def processar_relatorio_imediato(self):
        try:
            self.processing = True
            self.save()
            
            print(f"🔍 INICIANDO PROCESSAMENTO do relatório {self.id}")
            
            sensor_data = self.get_sensor_data()
            
            if self.has_minimum_data():
                print("✅ Dados mínimos atendidos pelos sensores")
                risco_detectado = self._verificar_risco_por_requisitos()
                self.risk_alert = risco_detectado
                
                print("🔄 Processando modelos matemáticos...")
                self._processar_modelos_matematicos()
            else:
                print(f"❌ Dados insuficientes dos sensores para processamento")
                self.risk_alert = False
            
            self.processed = True
            self.processing = False
            self.save()
            
        except Exception as e:
            print(f"❌ Erro no processamento do relatório {self.id}: {e}")
            self.processed = True
            self.processing = False
            self.risk_alert = False
            self.save()

    def _verificar_risco_por_requisitos(self):
        try:
            from .math_model import MathModel
            math_models = MathModel.objects.filter(stations=self.station, is_active=True)
            
            print(f"🔍 Verificando {math_models.count()} modelos para {self.station.alias}")

            for math_model in math_models:
                print(f"🔍 Analisando requisitos do modelo: {math_model.name}")
                
                if self._verificar_requisitos_do_modelo(math_model):
                    print(f"✅✅✅ REQUISITOS ATENDIDOS - Risco detectado!")
                    return True
            
            print(f"❌ Nenhum modelo atende aos requisitos")
            return False
            
        except Exception as e:
            print(f"❌ Erro ao verificar risco: {e}")
            return False

    def _processar_modelos_matematicos(self):
        try:
            from .math_model import MathModel
            
            math_models = MathModel.objects.filter(
                stations=self.station,
                is_active=True
            )

            print(f"🔍 Processando {math_models.count()} modelos matemáticos")

            for math_model in math_models:
                try:
                    if not self._verificar_requisitos_do_modelo(math_model):
                        print(f"❌ Modelo {math_model.name} não atende requisitos - pulando")
                        continue
                    
                    print(f"🔍 Processando modelo: {math_model.name}")
                    
                    resultado = math_model.process_accumulation(self.station, self)
                    
                    if resultado:
                        if resultado.is_alert_triggered:
                            print(f"🚨🚨🚨 ALERTA DISPARADO por {math_model.name}!")
                        else:
                            print(f"ℹ️ Modelo {math_model.name} processado - sem alerta")
                    else:
                        print(f"❌ process_accumulation retornou None para {math_model.name}")
                        
                except Exception as e:
                    print(f"❌ Erro no modelo {math_model.name}: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Erro no processamento de modelos matemáticos: {e}")

    def _verificar_requisitos_do_modelo(self, math_model):
        try:
            if not math_model.requirements.exists():
                print(f"🔍 Modelo {math_model.name} não tem requisitos - considerado atendido")
                return True
            
            for requirement in math_model.requirements.all():
                if not requirement.is_active:
                    continue
                    
                atendido = requirement.validate_for_report(self)
                print(f"🔍 Requisito {requirement.name}: {atendido}")
                
                if not atendido:
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao verificar requisitos do modelo {math_model.name}: {e}")
            return False

    def processar_relatorio(self):
        self.processar_relatorio_imediato()

    class Meta:
        verbose_name = "Relatório"
        verbose_name_plural = "Relatórios"
        ordering = ['-time']