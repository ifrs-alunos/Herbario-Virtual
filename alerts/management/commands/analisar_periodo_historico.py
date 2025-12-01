from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from alerts.models import Station, Report
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Analisa novembro de 2024 para janelas de 6h com temperatura 17-26°C e umidade >85%'

    def add_arguments(self, parser):
        parser.add_argument(
            '--estacao',
            type=str,
            help='Alias da estação a ser analisada (opcional)',
        )

    def handle(self, *args, **options):
        estacao_alias = options.get('estacao')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🔍 ANALISANDO NOVEMBRO 2024 - JANELAS DE 6H'
            )
        )
        self.stdout.write('📋 Requisitos: Temperatura 17-26°C, Umidade >85%, 6h consecutivas')
        self.stdout.write('=' * 80)

        # Definir período de análise: todo novembro 2024
        data_inicio = datetime(2024, 11, 1, 0, 0, 0)
        data_fim = datetime(2024, 11, 30, 23, 59, 59)
        
        # Ajustar timezone se necessário
        if timezone.is_naive(data_inicio):
            data_inicio = timezone.make_aware(data_inicio)
            data_fim = timezone.make_aware(data_fim)

        # Obter estações para análise
        if estacao_alias:
            estacoes = Station.objects.filter(alias=estacao_alias)
        else:
            estacoes = Station.objects.all()

        if not estacoes.exists():
            self.stdout.write(
                self.style.ERROR('❌ Nenhuma estação encontrada!')
            )
            return

        for estacao in estacoes:
            self.analisar_estacao(estacao, data_inicio, data_fim)

    def analisar_estacao(self, estacao, data_inicio, data_fim):
        """Analisa uma estação específica"""
        self.stdout.write(
            self.style.SUCCESS(f'\n📍 ANALISANDO ESTAÇÃO: {estacao.alias}')
        )

        # Buscar todos os relatórios do período
        relatorios = Report.objects.filter(
            station=estacao,
            time__range=(data_inicio, data_fim)
        ).order_by('time')

        self.stdout.write(f'📊 Total de relatórios encontrados: {relatorios.count()}')

        if relatorios.count() == 0:
            self.stdout.write(self.style.WARNING('⚠️  Nenhum relatório encontrado para análise'))
            return

        # Analisar períodos consecutivos
        periodos_favoraveis = self.analisar_periodos_consecutivos(relatorios)
        
        # Filtrar apenas períodos com 6+ horas
        periodos_6h_plus = [p for p in periodos_favoraveis if self.calcular_duracao_horas(p) >= 6]
        
        # Exibir resultados
        self.exibir_resultados(periodos_6h_plus, estacao)

    def analisar_periodos_consecutivos(self, relatorios):
        """Analisa períodos consecutivos que atendem aos requisitos"""
        periodos_favoraveis = []
        periodo_atual = []
        ultimo_relatorio = None
        
        for relatorio in relatorios:
            dados = relatorio.get_sensor_data()
            temperatura = dados.get('t')
            umidade = dados.get('rh')
            
            # Verificar se atende aos requisitos
            atende_requisitos = self.verificar_requisitos_fungo(temperatura, umidade)
            
            if atende_requisitos:
                # Se é o primeiro relatório do período ou continuação
                if not periodo_atual:
                    periodo_atual = {
                        'inicio': relatorio.time,
                        'fim': relatorio.time,
                        'relatorios': [relatorio],
                        'temperaturas': [temperatura],
                        'umidades': [umidade]
                    }
                else:
                    # Verificar se há gap muito grande (resetar se > 2 horas)
                    if ultimo_relatorio:
                        gap_horas = (relatorio.time - ultimo_relatorio.time).total_seconds() / 3600
                        if gap_horas > 2:
                            # Finalizar período anterior e iniciar novo
                            if self.calcular_duracao_horas(periodo_atual) >= 0.5:
                                periodos_favoraveis.append(periodo_atual)
                            periodo_atual = {
                                'inicio': relatorio.time,
                                'fim': relatorio.time,
                                'relatorios': [relatorio],
                                'temperaturas': [temperatura],
                                'umidades': [umidade]
                            }
                        else:
                            # Continuar período atual
                            periodo_atual['fim'] = relatorio.time
                            periodo_atual['relatorios'].append(relatorio)
                            periodo_atual['temperaturas'].append(temperatura)
                            periodo_atual['umidades'].append(umidade)
                    else:
                        # Continuar período atual
                        periodo_atual['fim'] = relatorio.time
                        periodo_atual['relatorios'].append(relatorio)
                        periodo_atual['temperaturas'].append(temperatura)
                        periodo_atual['umidades'].append(umidade)
            else:
                # Não atende requisitos - finalizar período atual se existir
                if periodo_atual and self.calcular_duracao_horas(periodo_atual) >= 0.5:
                    periodos_favoraveis.append(periodo_atual)
                periodo_atual = []
            
            ultimo_relatorio = relatorio

        if periodo_atual and self.calcular_duracao_horas(periodo_atual) >= 0.5:
            periodos_favoraveis.append(periodo_atual)

        return periodos_favoraveis

    def verificar_requisitos_fungo(self, temperatura, umidade):
        """Verifica se temperatura e umidade atendem aos requisitos do fungo"""
        if temperatura is None or umidade is None:
            return False
        
        temp_ok = 17 <= temperatura <= 26
        
        umidade_ok = umidade >= 85
        
        return temp_ok and umidade_ok

    def calcular_duracao_horas(self, periodo):
        """Calcula a duração de um período em horas"""
        if not periodo or 'inicio' not in periodo or 'fim' not in periodo:
            return 0
        
        duracao_segundos = (periodo['fim'] - periodo['inicio']).total_seconds()
        return duracao_segundos / 3600

    def exibir_resultados(self, periodos_6h_plus, estacao):
        """Exibe apenas os períodos que atingiram 6+ horas"""
        if not periodos_6h_plus:
            self.stdout.write(
                self.style.WARNING('❌ Nenhuma janela de 6+ horas encontrada!')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'🎯 JANELAS DE 6+ HORAS ENCONTRADAS: {len(periodos_6h_plus)}')
        )

        for i, periodo in enumerate(periodos_6h_plus, 1):
            duracao_horas = self.calcular_duracao_horas(periodo)
            relatorios_count = len(periodo['relatorios'])
            
            temp_media = sum(periodo['temperaturas']) / len(periodo['temperaturas'])
            umidade_media = sum(periodo['umidades']) / len(periodo['umidades'])
            
            temp_min = min(periodo['temperaturas'])
            temp_max = max(periodo['temperaturas'])
            umidade_min = min(periodo['umidades'])
            umidade_max = max(periodo['umidades'])

            self.stdout.write(f'\n📅 JANELA {i}:')
            self.stdout.write(f'   🕐 Início: {periodo["inicio"].strftime("%d/%m %H:%M")}')
            self.stdout.write(f'   🕐 Fim:    {periodo["fim"].strftime("%d/%m %H:%M")}')
            self.stdout.write(f'   ⏱️  Duração: {duracao_horas:.1f} horas')
            self.stdout.write(f'   📊 Relatórios: {relatorios_count}')
            self.stdout.write(f'   🌡️  Temp: {temp_media:.1f}°C (min: {temp_min:.1f}°C, max: {temp_max:.1f}°C)')
            self.stdout.write(f'   💧 Umidade: {umidade_media:.1f}% (min: {umidade_min:.1f}%, max: {umidade_max:.1f}%)')
            self.stdout.write(self.style.SUCCESS('   ✅ ATINGIU 6h+ - CONDIÇÕES IDEAIS PARA FUNGO'))

        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(
            self.style.SUCCESS(
                f'📈 RESUMO FINAL - {estacao.alias}:'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'   🎯 Janelas de 6+ horas: {len(periodos_6h_plus)}'
            )
        )
        
        total_horas_favoraveis = sum(self.calcular_duracao_horas(p) for p in periodos_6h_plus)
        self.stdout.write(
            self.style.SUCCESS(
                f'   ⏱️  Total de horas favoráveis: {total_horas_favoraveis:.1f}h'
            )
        )
        
        total_relatorios_favoraveis = sum(len(p['relatorios']) for p in periodos_6h_plus)
        self.stdout.write(
            self.style.SUCCESS(
                f'   📊 Total de relatórios favoráveis: {total_relatorios_favoraveis}'
            )
        )

        if len(periodos_6h_plus) > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    '🚨 ALERTA: Condições ideais para formação do fungo foram atingidas!'
                )
            )