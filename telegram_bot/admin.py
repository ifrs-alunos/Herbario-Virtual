from django.contrib import admin
from django.utils.html import format_html
from .models import TelegramUser, TelegramPhoto


class VinculoFilter(admin.SimpleListFilter):
    """Filtra conversas por terem ou não uma conta do sistema vinculada"""

    title = "vínculo com conta"
    parameter_name = "vinculado"

    def lookups(self, request, model_admin):
        return (('sim', 'Vinculado'), ('nao', 'Não vinculado'))

    def queryset(self, request, queryset):
        if self.value() == 'sim':
            return queryset.filter(profile__isnull=False)
        if self.value() == 'nao':
            return queryset.filter(profile__isnull=True)
        return queryset


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'username', 'first_name', 'conta_vinculada',
                    'is_active', 'recebe_alertas', 'subscribed_at', 'last_alert_sent')
    search_fields = ('chat_id', 'username', 'first_name',
                     'profile__name', 'profile__user__username', 'profile__user__email')
    list_filter = ('is_active', VinculoFilter, 'subscribed_at')
    list_select_related = ('profile', 'profile__user')
    raw_id_fields = ('profile',)
    readonly_fields = ('subscribed_at', 'linked_at', 'last_alert_sent')
    actions = ['desvincular_conta']

    def conta_vinculada(self, obj):
        if obj.profile_id is None:
            return "—"
        return obj.profile.user.username
    conta_vinculada.short_description = "Conta vinculada"
    conta_vinculada.admin_order_field = 'profile__user__username'

    def recebe_alertas(self, obj):
        return obj.receives_alerts
    recebe_alertas.boolean = True
    recebe_alertas.short_description = "Recebe alertas"

    def desvincular_conta(self, request, queryset):
        """Solta o vínculo para que outra conversa possa reivindicar a mesma conta.

        É a saída para quem trocou de conta do Telegram e recebe a mensagem de
        "@ já vinculado a outra conversa".
        """
        total = queryset.update(profile=None, linked_at=None)
        self.message_user(request, "{} conversa(s) desvinculada(s).".format(total))
    desvincular_conta.short_description = "Desvincular conta do sistema"


@admin.register(TelegramPhoto)
class TelegramPhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'telegram_user', 'source', 'received_at', 'preview')
    list_filter = ('source', 'received_at')
    search_fields = ('telegram_user__chat_id', 'telegram_user__username',
                     'telegram_user__first_name', 'telegram_user__profile__name', 'caption')
    readonly_fields = (
        'telegram_user', 'image', 'preview', 'width', 'height', 'file_id', 'file_unique_id',
        'file_size', 'caption', 'telegram_message_id', 'media_group_id', 'source', 'received_at',
    )

    def preview(self, obj):
        """Mostra uma miniatura da imagem recebida"""
        if obj.image:
            return format_html('<img src="{}" style="max-height:150px">', obj.image.url)
        return "-"

    preview.short_description = "Pré-visualização"
