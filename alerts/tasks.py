import logging
from django.utils import timezone
from celery import shared_task
from django.db import models

logger = logging.getLogger(__name__)

@shared_task
def check_scheduled_alerts():
    """Task periódica para verificar alertas agendados - VERSÃO CORRIGIDA"""
    from alerts.models.tempo_de_analise import ConditionWindow
    from django.utils import timezone
    
    try:
        current_time = timezone.now()
        print(f"🔍 VERIFICANDO ALERTAS AGENDADOS às {current_time}")
        
        # Busca TODAS as janelas com alertas agendados
        pending_windows = ConditionWindow.objects.filter(
            is_accumulation_active=True,
            expected_alert_time__isnull=False,
            current_accumulated_value__gte=models.F('math_model__alert_threshold')
        ).select_related('math_model', 'station')
        
        print(f"📋 Janelas elegíveis para alerta: {pending_windows.count()}")
        
        alertas_disparados = 0
        for window in pending_windows:
            print(f"\n🔎 Analisando: {window.math_model.name} - {window.station.alias}")
            print(f"   ⏰ Agendado para: {window.expected_alert_time}")
            print(f"   ✅ Já passou? {current_time >= window.expected_alert_time}")
            print(f"   📈 Acumulado: {window.current_accumulated_value:.3f}")
            print(f"   🎯 Threshold: {window.math_model.alert_threshold}")
            
            # VERIFICAÇÃO DIRETA - se passou do tempo, DISPARA
            if current_time >= window.expected_alert_time:
                print(f"🚨🚨🚨 TEMPO ATINGIDO - DISPARANDO ALERTA!")
                try:
                    window.math_model._trigger_alert_from_window(window)
                    alertas_disparados += 1
                    print(f"✅ Alerta disparado com sucesso!")
                except Exception as e:
                    print(f"❌ Erro ao disparar alerta: {e}")
            else:
                tempo_restante = window.expected_alert_time - current_time
                print(f"⏳ Aguardando: {tempo_restante}")
        
        print(f"\n📊 RESUMO: {alertas_disparados} alerta(s) disparado(s)")
        return alertas_disparados
                
    except Exception as e:
        print(f"❌ Erro geral na verificação de alertas: {e}")
        return 0

@shared_task
def system_status():
    """Task para verificar status do sistema (não apaga dados)"""
    from alerts.models.alert_history import AlertHistory
    from alerts.models.mathmodel_result import MathModelResult
    from alerts.models.tempo_de_analise import ConditionWindow
    
    try:
        stats = {
            'total_alerts': AlertHistory.objects.count(),
            'total_results': MathModelResult.objects.count(),
            'active_windows': ConditionWindow.objects.filter(is_accumulation_active=True).count(),
            'pending_alerts': ConditionWindow.objects.filter(
                is_accumulation_active=True,
                expected_alert_time__isnull=False
            ).count(),
        }
        
        print(f"📊 Status do Sistema: {stats}")
        return stats
        
    except Exception as e:
        print(f"❌ Erro no status: {e}")
        return {'error': str(e)}