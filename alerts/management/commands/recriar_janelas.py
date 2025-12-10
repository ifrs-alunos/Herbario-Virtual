# management/commands/recriar_janelas.py
from django.core.management.base import BaseCommand
from alerts.models import MathModel, AnalysisWindow, Report
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Recriar todas as janelas de análise'
    
    def handle(self, *args, **options):
        self.stdout.write('🔄 Recriando janelas de análise...')
        
        AnalysisWindow.objects.all().delete()
        self.stdout.write('🧹 Janelas antigas removidas')
        
        modelos = MathModel.objects.filter(is_active=True)
        
        for modelo in modelos:
            self.stdout.write(f'🔧 Processando modelo: {modelo.name}')
            
            relatorios = Report.objects.filter(
                station__in=modelo.stations.all(),
                time__gte=timezone.now() - timedelta(days=1)
            ).order_by('time')
            
            for relatorio in relatorios:
                # Verifica se o relatório tem dados válidos através das leituras dos sensores
                relatorio_data = modelo._extract_data_from_readings(relatorio)
                has_valid_temp = relatorio_data['t'] != 0 and -50 <= relatorio_data['t'] <= 60
                has_valid_humidity = relatorio_data['rh'] != 0 and 0 <= relatorio_data['rh'] <= 100

                if has_valid_temp and has_valid_humidity:
                    resultado = modelo.process_accumulation(relatorio.station, relatorio)
                    if resultado:
                        status = "ALERTA" if resultado.is_alert_triggered else "normal"
                        self.stdout.write(f'   📊 Relatório {relatorio.id}: {resultado.accumulated_value:.3f} - {status}')
        
        self.stdout.write('✅ Janelas recriadas com sucesso!')