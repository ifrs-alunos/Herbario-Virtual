from django.contrib import admin
from .models import Solicitation, Profile
# from .models import PhotoSolicitation, PlantSolicitation, DiseaseSolicitation,\
# 	CharSolicitationModel, DiseasePhotoSolicitation

# Register your models here.

admin.site.register(Solicitation)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'institution', 'role', 'telegram_username',
                    'telegram_vinculado')
    search_fields = ('name', 'user__username', 'user__email', 'institution',
                     'telegram_username')
    list_filter = ('institution',)
    list_select_related = ('user',)
    filter_horizontal = ('alerts_for_diseases',)

    def telegram_vinculado(self, obj):
        telegram_user = getattr(obj, 'telegram_user', None)
        if telegram_user is None:
            return "—"
        return telegram_user.username or telegram_user.first_name or telegram_user.chat_id
    telegram_vinculado.short_description = "Telegram vinculado"

# admin.site.register(PlantSolicitation)
# admin.site.register(PhotoSolicitation)
# admin.site.register(DiseaseSolicitation)
# admin.site.register(CharSolicitationModel)
# admin.site.register(DiseasePhotoSolicitation)
