# management/commands/testar_disparo.py
from django.core.management.base import BaseCommand
from alerts.models import MathModel, Station, Report
from django.utils import timezone

class Command(BaseCommand):
    help = 'Testar o disparo de alertas'
    
    def handle(self, *args, **options):
        self.stdout.write('🚀 Testando disparo de alertas...')
        
        # Buscar um modelo ativo com threshold
        modelos = MathModel.objects.filter(
            is_active=True, 
            alert_threshold__isnull=False
        )
        
        if not modelos.exists():
            self.stdout.write('❌ Nenhum modelo ativo com threshold encontrado')
            return
        
        for modelo in modelos:
            self.stdout.write(f'🔍 Testando modelo: {modelo.name} (Threshold: {modelo.alert_threshold})')
            
            # Buscar estações associadas
            for estacao in modelo.stations.all():
                self.stdout.write(f'📍 Estação: {estacao.alias}')
                
                # Buscar relatório recente
                relatorio = Report.objects.filter(
                    station=estacao
                ).order_by('-time').first()
                
                if relatorio:
                    self.stdout.write(f'📊 Relatório {relatorio.id} encontrado')
                    
                    # Testar processamento
                    resultado = modelo.process_accumulation(estacao, relatorio)
                    
                    if resultado:
                        status = "ALERTA" if resultado.is_alert_triggered else "normal"
                        self.stdout.write(f'✅ Resultado: {resultado.accumulated_value:.3f} - {status}')
                    else:
                        self.stdout.write('❌ Falha no processamento')
                else:
                    self.stdout.write('⚠️ Nenhum relatório encontrado')