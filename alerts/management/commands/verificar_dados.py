# management/commands/verificar_dados.py
from django.core.management.base import BaseCommand
from alerts.models import Report

class Command(BaseCommand):
    help = 'Verificar dados dos relatórios'
    
    def handle(self, *args, **options):
        self.stdout.write('🔍 Verificando dados dos relatórios...')
        
        relatorios = Report.objects.all().order_by('-id')[:10]
        
        for relatorio in relatorios:
            self.stdout.write(f'\n📊 Relatório {relatorio.id}:')
            self.stdout.write(f'   🕐 Time: {relatorio.time}')
            self.stdout.write(f'   🏠 Station: {relatorio.station.alias}')
            self.stdout.write(f'   🌡️ Temperatura: {relatorio.temperatura}')
            self.stdout.write(f'   💧 Umidade: {relatorio.umidade}')
            self.stdout.write(f'   📖 Reading Temp: {relatorio.reading_temp}')
            self.stdout.write(f'   📖 Reading Humidity: {relatorio.reading_humidity}')
            self.stdout.write(f'   ✅ Processado: {relatorio.processed}')