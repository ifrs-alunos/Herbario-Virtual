from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
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


class UsoFilter(admin.SimpleListFilter):
    """Filtra imagens pelo uso escolhido, incluindo as que ainda aguardam resposta"""

    title = "uso no modelo"
    parameter_name = "uso"

    def lookups(self, request, model_admin):
        return TelegramPhoto.PURPOSE_CHOICES + [
            ('pendente', 'Aguardando escolha'),
            ('descricao', 'Treino aguardando descrição'),
            ('revisao', 'Treino aguardando aprovação'),
            ('aprovada', 'Treino aprovado'),
            ('reprovada', 'Treino reprovado'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'pendente':
            return queryset.pending()
        if self.value() == 'descricao':
            return queryset.awaiting_description()
        if self.value() == 'revisao':
            return queryset.awaiting_approval()
        if self.value() == 'aprovada':
            return queryset.approved()
        if self.value() == 'reprovada':
            return queryset.rejected()
        if self.value():
            return queryset.filter(purpose=self.value())
        return queryset


@admin.register(TelegramPhoto)
class TelegramPhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'telegram_user', 'purpose', 'review_status', 'disease', 'disease_state', 'source',
                    'received_at', 'preview')
    list_filter = (UsoFilter, 'source', 'received_at', 'disease')
    list_select_related = ('telegram_user', 'disease')
    search_fields = ('telegram_user__chat_id', 'telegram_user__username',
                     'telegram_user__first_name', 'telegram_user__profile__name', 'caption', 'description')
    # O widget padrão do FileField usa .url, que media-ia/ não tem: o caminho
    # aparece em caminho_arquivo e a imagem em preview.
    exclude = ('image',)
    readonly_fields = (
        'telegram_user', 'purpose', 'caminho_arquivo', 'preview', 'width', 'height', 'file_name',
        'file_id', 'file_unique_id', 'file_size', 'caption', 'telegram_message_id',
        'media_group_id', 'source', 'received_at', 'classified_at', 'description_number',
        'awaiting_description', 'description', 'disease', 'disease_state', 'review_status', 'reviewed_at', 'reviewed_by',
    )

    def get_urls(self):
        urls = [
            path('<int:pk>/arquivo/', self.admin_site.admin_view(self.arquivo_view),
                 name='telegram_bot_telegramphoto_arquivo'),
        ]
        return urls + super().get_urls()

    def arquivo_view(self, request, pk):
        """Entrega o arquivo de media-ia/, que não tem URL pública, a quem pode ver o registro"""

        if not self.has_view_permission(request):
            raise PermissionDenied

        photo = get_object_or_404(TelegramPhoto, pk=pk)
        if not photo.image:
            raise Http404("Imagem ainda não baixada")

        return FileResponse(photo.image.open('rb'))

    def caminho_arquivo(self, obj):
        return "media-ia/{}".format(obj.image.name) if obj.image else "-"

    caminho_arquivo.short_description = "Arquivo"

    def preview(self, obj):
        """Mostra uma miniatura da imagem recebida"""
        if obj.image:
            url = reverse('admin:telegram_bot_telegramphoto_arquivo', args=[obj.pk])
            return format_html('<img src="{}" style="max-height:150px">', url)
        return "-"

    preview.short_description = "Pré-visualização"
