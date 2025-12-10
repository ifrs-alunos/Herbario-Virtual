# alerts/management/commands/clean_today_results.py
from django.core.management.base import BaseCommand
from alerts.models import MathModelResult
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Limpa APENAS resultados de modelos matemáticos de HOJE'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirma a exclusão (sem este parâmetro, apenas mostra o que será deletado)',
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Filtrar por nome do modelo (opcional)',
        )
        parser.add_argument(
            '--station', 
            type=str,
            help='Filtrar por nome da estação (opcional)',
        )

    def handle(self, *args, **options):
        # Define o intervalo de HOJE (00:00 até agora)
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = timezone.now()
        
        # Encontra resultados de hoje
        today_results = MathModelResult.objects.filter(date__gte=today_start, date__lte=today_end)
        
        # Aplica filtros adicionais
        if options['model']:
            today_results = today_results.filter(mathmodel__name__icontains=options['model'])
            self.stdout.write(f"🔍 Filtrando por modelo: {options['model']}")
        
        if options['station']:
            today_results = today_results.filter(station__alias__icontains=options['station'])
            self.stdout.write(f"🔍 Filtrando por estação: {options['station']}")
        
        count = today_results.count()
        
        if count == 0:
            self.stdout.write(
                self.style.WARNING('ℹ️ Nenhum resultado encontrado para hoje com os filtros especificados')
            )
            return
        
        if not options['confirm']:
            # Modo preview - mostra o que será deletado
            self.stdout.write(
                self.style.WARNING(f'🚨 ENCONTRADOS {count} resultados de HOJE ({today_start.date()}):')
            )
            
            # Mostra alguns exemplos
            for result in today_results[:3]:
                self.stdout.write(
                    f"   • {result.mathmodel.name} - {result.station.alias} - "
                    f"{result.date.strftime('%H:%M:%S')} - Acumulado: {result.accumulated_value:.2f}"
                )
            
            if count > 3:
                self.stdout.write(f"   ... e mais {count - 3} resultados")
            
            # Estatísticas
            models_count = today_results.values('mathmodel__name').distinct().count()
            stations_count = today_results.values('station__alias').distinct().count()
            
            self.stdout.write(f"\n📊 Estatísticas:")
            self.stdout.write(f"   • Modelos diferentes: {models_count}")
            self.stdout.write(f"   • Estações diferentes: {stations_count}")
            
            self.stdout.write(
                self.style.ERROR('\n⚠️  Para realmente DELETAR, execute:')
            )
            self.stdout.write(
                self.style.ERROR(f'python manage.py clean_today_results --confirm')
            )
            
            if options['model']:
                self.stdout.write(
                    self.style.ERROR(f'python manage.py clean_today_results --model "{options["model"]}" --confirm')
                )
            if options['station']:
                self.stdout.write(
                    self.style.ERROR(f'python manage.py clean_today_results --station "{options["station"]}" --confirm')
                )
            return
        
        # Modo de exclusão real
        deleted_count = count
        today_results.delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ {deleted_count} resultados de HOJE ({today_start.date()}) foram removidos com sucesso!'
            )
        )
