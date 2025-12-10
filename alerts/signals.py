from django.db.models.signals import post_save
from django.dispatch import receiver
from alerts.models import Reading
import threading
import time

processing_lock = threading.Lock()
currently_processing = set()

@receiver(post_save, sender=Reading)
def processar_apos_reading(sender, instance, created, **kwargs):
    """
    Processa o relatório quando um READING é criado
    """
    if not created or not instance.report:
        return
        
    report_id = instance.report.id
    
    def processar_com_verificacao():
        with processing_lock:
            if report_id in currently_processing:
                print(f"⚡ Relatório {report_id} já está sendo processado - ignorando")
                return
            currently_processing.add(report_id)
        
        try:
            from alerts.models.report import Report
            try:
                report = Report.objects.get(id=report_id)
            except Report.DoesNotExist:
                print(f"❌ Relatório {report_id} não existe mais")
                return
                
            report.refresh_from_db()
            
            print(f"🎯 Processando relatório {report.id} (via signal)")
            print(f"   Hora: {report.time}")
            print(f"   Readings: {report.readings.count()}")
            
            sensor_data = report.get_sensor_data()
            has_min_data = sensor_data['t'] is not None and sensor_data['rh'] is not None
            
            if has_min_data and not report.processed:
                print(f"🚀 Iniciando processamento...")
                report.processar_relatorio_imediato()
            elif report.processed:
                print(f"✅ Já processado")
            else:
                print(f"❌ Sem dados mínimos")
                
        except Exception as e:
            print(f"❌ Erro no signal: {e}")
        finally:
            with processing_lock:
                currently_processing.discard(report_id)
    
    import threading
    import time
    time.sleep(1)
    
    thread = threading.Thread(target=processar_com_verificacao)
    thread.daemon = True
    thread.start()