from django.core.management.base import BaseCommand
from django.utils import timezone
from alerts.models import MathModel, Station
from alerts.models.mathmodel_result import MathModelResult
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Zera APENAS os valores acumulados dos MathModelResults'

    def add_arguments(self, parser):
        parser.add_argument(
            '--estacao',
            type=str,
            default='Fazenda Lagoão',
            help='Estação específica (padrão: Fazenda Lagoão)'
        )
        parser.add_argument(
            '--modelo',
            type=str, 
            default='Favorabilidade para ferrugem da soja',
            help='Modelo específico (padrão: Favorabilidade para ferrugem da soja)'
        )
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirmar a operação (OBRIGATÓRIO)'
        )

    def handle(self, *args, **options):
        estacao_alias = options['estacao']
        modelo_nome = options['modelo']
        confirmar = options['confirmar']
        
        self.stdout.write(
            self.style.WARNING(
                f'⚠️  ZERAR ACUMULADOS: {modelo_nome} - {estacao_alias}'
            )
        )
        self.stdout.write('🎯 Ação: Zerar APENAS accumulated_value (valores grandes como 274.513)')
        self.stdout.write('=' * 80)

        if not confirmar:
            self.stdout.write(self.style.ERROR(
                '❌ CONFIRMAÇÃO OBRIGATÓRIA! Use --confirmar para executar'
            ))
            self.stdout.write('💡 Comando completo:')
            self.stdout.write(f'   python manage.py zerar_apenas_acumulados --confirmar')
            return

        try:
            with transaction.atomic():
                # Buscar estação e modelo
                estacao = Station.objects.get(alias=estacao_alias)
                modelo = MathModel.objects.get(name=modelo_nome)
                
                self.stdout.write(f'🔍 Buscando MathModelResults...')
                self.stdout.write(f'   📍 Estação: {estacao.alias}')
                self.stdout.write(f'   🔧 Modelo: {modelo.name}')

                # Buscar TODOS os resultados para esta estação/modelo
                mathmodel_results = MathModelResult.objects.filter(
                    mathmodel=modelo,
                    station=estacao
                ).order_by('date')

                total_results = mathmodel_results.count()
                
                if total_results == 0:
                    self.stdout.write(self.style.WARNING('❌ Nenhum MathModelResult encontrado!'))
                    return

                # 🔥 ANALISAR ANTES DE ZERAR
                self.stdout.write(f'\n📊 ANÁLISE ANTES DO ZERAMENTO:')
                
                # Encontrar o maior acumulado
                maior_acumulado = mathmodel_results.order_by('-accumulated_value').first()
                if maior_acumulado:
                    self.stdout.write(f'   📈 Maior acumulado: {maior_acumulado.accumulated_value:.3f}')
                    self.stdout.write(f'   📅 Data do maior: {maior_acumulado.date}')
                
                # Contar resultados com acumulado > 0
                com_acumulado = mathmodel_results.filter(accumulated_value__gt=0).count()
                self.stdout.write(f'   🔢 Resultados com acumulado > 0: {com_acumulado}/{total_results}')
                
                # Mostrar alguns exemplos de acumulados grandes
                acumulados_grandes = mathmodel_results.filter(accumulated_value__gt=100)[:5]
                if acumulados_grandes.exists():
                    self.stdout.write(f'\n   🚨 EXEMPLOS DE ACUMULADOS GRANDES:')
                    for result in acumulados_grandes:
                        self.stdout.write(f'      📅 {result.date.strftime("%d/%m %H:%M")}: {result.accumulated_value:.3f}')

                # 🔥 ZERAR APENAS OS ACUMULADOS
                self.stdout.write(f'\n🗑️  ZERANDO ACUMULADOS...')
                
                updated = mathmodel_results.update(
                    accumulated_value=0.0  # ⬅️ APENAS ISSO!
                    # NÃO mexe em: value, date, is_alert_triggered, etc.
                )
                
                self.stdout.write(f'   ✅ {updated} MathModelResults atualizados')
                self.stdout.write(f'   💾 accumulated_value = 0.0 para todos')

                # 🔥 VERIFICAR DEPOIS
                self.stdout.write(f'\n📊 VERIFICAÇÃO APÓS ZERAMENTO:')
                
                resultados_zerados = MathModelResult.objects.filter(
                    mathmodel=modelo,
                    station=estacao,
                    accumulated_value=0.0
                ).count()
                
                self.stdout.write(f'   ✅ Resultados com accumulated_value = 0.0: {resultados_zerados}/{total_results}')

                # 🔥 RELATÓRIO FINAL
                self.stdout.write('\n' + '=' * 80)
                self.stdout.write(self.style.SUCCESS('✅ ZERAMENTO CONCLUÍDO!'))
                self.stdout.write('=' * 80)
                
                self.stdout.write(f'🎯 AÇÃO REALIZADA:')
                self.stdout.write(f'   📍 Estação: {estacao.alias}')
                self.stdout.write(f'   🔧 Modelo: {modelo.name}')
                self.stdout.write(f'   📊 MathModelResults: {updated} atualizados')
                self.stdout.write(f'   💰 accumulated_value: 0.0 para todos')
                
                self.stdout.write(f'\n💡 O QUE FOI MANTIDO:')
                self.stdout.write(f'   ✅ value (valor calculado por relatório)')
                self.stdout.write(f'   ✅ date (data/hora do relatório)') 
                self.stdout.write(f'   ✅ is_alert_triggered (histórico de alertas)')
                self.stdout.write(f'   ✅ Todos os registros históricos')
                
                self.stdout.write(f'\n🚀 PRÓXIMOS PASSOS:')
                self.stdout.write(f'   🔄 O sistema recomeçará acumulação do zero')
                self.stdout.write(f'   📈 Novos acumulados serão calculados corretamente')
                self.stdout.write(f'   🎯 Lógica de 6h contínuas funcionará normalmente')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro durante o zeramento: {e}'))
            import traceback
            traceback.print_exc()