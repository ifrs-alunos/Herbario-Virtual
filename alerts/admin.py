from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html
from django.utils.timezone import localtime
from django import forms
from django.db import models
from .models import (
    Report,
    Station,
    Sensor,
    MathModel,
    Requirement,
    TypeSensor,
    Reading,
    SensorInMathModel,
    Constant,
    MathModelResult,
    UserAlert,
    AlertHistory,
    MathModelRequirement,
)

class MathModelForm(forms.ModelForm):
    class Meta:
        model = MathModel
        fields = '__all__'
        widgets = {
            'source_code': forms.Textarea(attrs={'rows': 4, 'cols': 80}),
            'alert_message': forms.Textarea(attrs={'rows': 3, 'cols': 80}),
        }

class RequirementForm(forms.ModelForm):
    class Meta:
        model = Requirement
        fields = '__all__'
        widgets = {
            'custom_expression': forms.Textarea(attrs={'rows': 3, 'cols': 80}),
        }

class ReadingInline(admin.TabularInline):
    model = Reading
    extra = 0
    fields = ('sensor', 'value', 'time')
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj is None and 'report' in formset.form.base_fields:
            formset.form.base_fields['report'].required = False
        return formset

@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = ("sensor", "value", "time", "report")
    search_fields = ("sensor__name", "time")
    list_filter = ("sensor", "time")
    ordering = ("-time",)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('station', 'formatted_time', 
                   'sensor_temp_display', 'sensor_humidity_display', 'sensor_rain_display',
                   'risco_display', 'risk_status')
    
    list_filter = ('station', 'risk_alert')
    search_fields = ('station__alias',)
    date_hierarchy = 'time'
    readonly_fields = ('risco_display', 'risk_status', 'sensor_data_display')
    
    inlines = [ReadingInline]
    
    actions = ['marcar_como_risco']
    
    fieldsets = (
        (None, {
            'fields': ('station', 'time')
        }),
        ('Leituras dos Sensores (Automático)', {
            'fields': ('sensor_data_display',),
            'description': 'Dados extraídos automaticamente dos sensores'
        }),
        ('Campos Manuais (Compatibilidade)', {
            'fields': ('reading_temp', 'reading_humidity', 'reading_rain'),
            'classes': ('collapse',),
            'description': 'Estes campos são opcionais - use apenas se necessário'
        }),
        ('Cálculos Automáticos', {
            'fields': ('risco_display', 'risk_alert', 'risk_status'),
            'classes': ('wide',)
        }),
    )

    @admin.display(description='Data/Hora')
    def formatted_time(self, obj):
        return localtime(obj.time).strftime('%d/%m/%Y %H:%M') if obj.time else 'Sem data'

    @admin.display(description='Temp. Sensor (°C)')
    def sensor_temp_display(self, obj):
        sensor_data = obj.get_sensor_data()
        return f"{sensor_data['t']:.1f}" if sensor_data['t'] is not None else "N/A"

    @admin.display(description='Umid. Sensor (%)')
    def sensor_humidity_display(self, obj):
        sensor_data = obj.get_sensor_data()
        return f"{sensor_data['rh']:.1f}" if sensor_data['rh'] is not None else "N/A"

    @admin.display(description='Chuva Sensor (mm)')
    def sensor_rain_display(self, obj):
        sensor_data = obj.get_sensor_data()
        return f"{sensor_data['rain']:.1f}" if sensor_data['rain'] is not None else "N/A"

    @admin.display(description='Dados dos Sensores')
    def sensor_data_display(self, obj):
        sensor_data = obj.get_sensor_data()
        return format_html(
            "🌡️ <b>Temp:</b> {}°C<br>"
            "💧 <b>Umidade:</b> {}%<br>"
            "🌧️ <b>Chuva:</b> {}mm",
            sensor_data['t'] if sensor_data['t'] is not None else "N/A",
            sensor_data['rh'] if sensor_data['rh'] is not None else "N/A", 
            sensor_data['rain'] if sensor_data['rain'] is not None else "N/A"
        )

    @admin.display(description='Temp. (°C)')
    def temperatura_display(self, obj):
        return f"{obj.temperatura:.1f}" if obj.temperatura is not None else "N/A"

    @admin.display(description='Umidade (%)')
    def umidade_display(self, obj):
        return f"{obj.umidade:.1f}" if obj.umidade is not None else "N/A"

    @admin.display(description='Chuva (h)')
    def tempo_chuva_display(self, obj):
        return f"{obj.tempo_chuva:.1f}" if obj.tempo_chuva is not None else "N/A"

    @admin.display(description='Status Risco', boolean=True)
    def risk_status(self, obj):
        return obj.risk_alert

    @admin.display(description='Valor Risco')
    def risco_display(self, obj):
        from alerts.models import MathModelResult
        resultados = MathModelResult.objects.filter(
            station=obj.station,
            date__date=obj.time.date(),
            accumulated_value__gt=0
        ).order_by('-accumulated_value')

        if not resultados.exists():
            return "N/A"

        max_result = resultados.first()
        color = "red" if obj.risk_alert else "green"
        formatted_value = f"{max_result.accumulated_value:.2f}"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            formatted_value
        )
    
    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)

            if not change or form.has_changed():
                self._processar_modelos_matematicos_admin(obj)

        except Exception as e:
            self.message_user(request, f"Erro ao salvar: {str(e)}", level=messages.ERROR)

    def _processar_modelos_matematicos_admin(self, relatorio):
        """Processa modelos matemáticos quando salvando relatório no admin"""
        try:
            from alerts.models import MathModel

            print(f"🔍 Processando modelos para relatório {relatorio.id} da estação {relatorio.station}")

            math_models = MathModel.objects.filter(
                stations=relatorio.station,
                is_active=True
            )

            print(f"🔍 Encontrados {math_models.count()} modelos ativos")

            alerta_disparado = False

            for math_model in math_models:
                try:
                    print(f"🔍 Processando modelo: {math_model.name}")

                    # Processa acumulação e cria MathModelResult
                    resultado = math_model.process_accumulation(relatorio.station, relatorio)

                    if resultado:
                        print(f"✅ MathModelResult criado: valor={resultado.value:.2f}, acumulado={resultado.accumulated_value:.2f}, alerta={resultado.is_alert_triggered}")

                        if resultado.is_alert_triggered:
                            print(f"🚨 ALERTA DISPARADO por {math_model.name}!")
                            # Dispara alertas - usa o mesmo método de extração de dados das leituras
                            current_data = math_model._extract_data_from_readings(relatorio)
                            math_model.trigger_alert(relatorio.station, resultado.accumulated_value, current_data)
                            alerta_disparado = True
                    else:
                        print(f"❌ process_accumulation retornou None para {math_model.name}")

                except Exception as e:
                    print(f"❌ Erro ao processar modelo {math_model.name}: {e}")

            if alerta_disparado and not relatorio.risk_alert:
                print(f"✅ Atualizando risk_alert para relatório {relatorio.id}")
                relatorio.risk_alert = True
                relatorio.save(update_fields=['risk_alert'])
            elif alerta_disparado:
                print(f"ℹ️ Relatório {relatorio.id} já tinha risk_alert=True")
            else:
                print(f"ℹ️ Nenhum alerta disparado para relatório {relatorio.id}")

        except Exception as e:
            print(f"❌ Erro geral ao processar modelos matemáticos: {e}")

    def marcar_como_risco(self, request, queryset):
        updated = queryset.update(risk_alert=True)
        self.message_user(
            request,
            f"{updated} relatório(s) marcado(s) como risco.",
            messages.SUCCESS
        )
    marcar_como_risco.short_description = "Marcar selecionados como risco"

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('alias', 'station_id', 'lat_coordinate', 'lon_coordinate')
    list_filter = ('alias',)
    search_fields = ('alias', 'station_id', 'description')

@admin.register(TypeSensor)
class TypeSensorAdmin(admin.ModelAdmin):
    list_display = ('name', 'metric')
    list_filter = ('metric',)
    search_fields = ('name',)

@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'station')
    list_filter = ('type', 'station')
    search_fields = ('name', 'station__alias')

class MathModelRequirementInline(admin.TabularInline):
    model = MathModelRequirement
    extra = 1
    fields = ('requirement', 'is_required', 'order')
    ordering = ('order',)

@admin.register(MathModel)
class MathModelAdmin(admin.ModelAdmin):
    form = MathModelForm
    list_display = [
        'name', 
        'disease',
        'evaluation_period', 
        'require_continuous_reports', 
        'alert_threshold', 
        'is_active',
        'require_minimum_hours',
        'min_conditions_hours',
        'retrospective_analysis_hours'
    ]
    list_editable = [
        'evaluation_period', 
        'require_continuous_reports', 
        'alert_threshold', 
        'is_active',
        'require_minimum_hours',
        'min_conditions_hours',
        'retrospective_analysis_hours'
    ]
    
    list_filter = ['disease', 'is_active', 'require_minimum_hours']
    
    filter_horizontal = ['stations']
    inlines = [MathModelRequirementInline]
    
    fieldsets = (
        ('Geral', {
            'fields': ('name', 'source_code', 'disease', 'stations', 'is_active')
        }),
        ('Configurações de Alerta', {
            'fields': ('evaluation_period', 'require_continuous_reports', 'alert_threshold', 'alert_message', 'min_positive_reports')
        }),
        ('Controle Temporal de Condições', {
            'fields': (
                'require_minimum_hours',
                'min_conditions_hours', 
                'accumulation_start_hours',
                'retrospective_analysis_hours'
            ),
            'description': 'Configurações de tempo mínimo para condições favoráveis'
        }),
    )

@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_parameter_display', 'get_operator_display', 'value', 'is_active']
    list_filter = ['parameter', 'operator', 'is_active']
    search_fields = ['name', 'custom_expression']
    list_editable = ['is_active']
    
    def get_parameter_display(self, obj):
        return obj.get_parameter_display()
    get_parameter_display.short_description = 'Parâmetro'
    
    def get_operator_display(self, obj):
        return obj.get_operator_display()
    get_operator_display.short_description = 'Operador'

@admin.register(SensorInMathModel)
class SensorInMathModelAdmin(admin.ModelAdmin):
    list_display = ('sensor', 'mathmodel', 'divider', 'in_graph')
    list_filter = ('mathmodel',)

@admin.register(Constant)
class ConstantAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'mathmodel')
    list_filter = ('mathmodel',)
    search_fields = ('name',)

@admin.register(MathModelResult)
class MathModelResultAdmin(admin.ModelAdmin):
    list_display = ('mathmodel', 'station', 'value', 'accumulated_value', 'is_alert_triggered', 'date')
    list_filter = ('mathmodel', 'station', 'is_alert_triggered', 'date')
    search_fields = ('mathmodel__name', 'station__alias')
    readonly_fields = ('value', 'accumulated_value', 'is_alert_triggered')
    
    def has_add_permission(self, request):
        return False

@admin.register(AlertHistory)
class AlertHistoryAdmin(admin.ModelAdmin):
    list_display = ('math_model', 'station', 'timestamp')
    list_filter = ('math_model', 'station')

@admin.register(UserAlert)
class UserAlertAdmin(admin.ModelAdmin):
    list_display = ("profile", "disease")
    list_filter = ("profile", "disease")

@admin.register(MathModelRequirement)
class MathModelRequirementAdmin(admin.ModelAdmin):
    list_display = ('math_model', 'requirement', 'is_required', 'order')
    list_filter = ('math_model', 'requirement', 'is_required')
    list_editable = ('is_required', 'order')
    
    fields = ('math_model', 'requirement', 'is_required', 'order')

from alerts.models.tempo_de_analise import ConditionWindow, AnalysisWindow, HourlyResult

@admin.register(ConditionWindow)
class ConditionWindowAdmin(admin.ModelAdmin):
    list_display = ('math_model', 'station', 'accumulation_start', 'current_accumulated_value', 'expected_alert_time', 'is_accumulation_active')
    list_filter = ('math_model', 'station', 'is_accumulation_active')
    search_fields = ('math_model__name', 'station__alias')
    readonly_fields = ('current_accumulated_value', 'accumulation_start', 'expected_alert_time')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('math_model', 'station', 'is_accumulation_active')
        }),
        ('Acumulação', {
            'fields': ('accumulation_start', 'current_accumulated_value', 'last_valid_report')
        }),
        ('Agendamento', {
            'fields': ('expected_alert_time',)
        }),
    )

@admin.register(AnalysisWindow)
class AnalysisWindowAdmin(admin.ModelAdmin):
    list_display = ('math_model', 'station', 'window_start', 'window_end', 'accumulated_value', 'is_complete')
    list_filter = ('math_model', 'station', 'is_complete')
    search_fields = ('math_model__name', 'station__alias')

@admin.register(HourlyResult)
class HourlyResultAdmin(admin.ModelAdmin):
    list_display = ('math_model', 'station', 'hour_start', 'value', 'accumulated_value', 'requirements_met')
    list_filter = ('math_model', 'station', 'requirements_met')
    search_fields = ('math_model__name', 'station__alias')