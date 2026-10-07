"""Módulo "Modelos de IA" do painel: revisão das imagens de treino enviadas ao bot.

O contribuidor (ou administrador) manda a imagem pelo Telegram, descreve o que
ela mostra e ela fica em media-ia/training/pending/. Aqui um administrador a
aprova escolhendo planta, doença e estado (o arquivo vai para
media-ia/training/approved/ com esses dados no nome) ou reprova (apaga registro e
arquivo, mantendo o registro com a decisão). As regras ficam em telegram_bot/services.py; estas views só recebem o
clique.
"""

from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from dashboard.forms import AIModelApprovalForm
from disease.models import Culture, Disease
from telegram_bot.models import TelegramPhoto
from telegram_bot.services import APPROVE_PERMISSION, approve_training_photo, reject_training_photo

__all__ = [
    'AIModelReviewListView',
    'ai_model_photo_file',
    'ai_model_photo_approve',
    'ai_model_photo_reject',
]


class AIModelReviewListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = APPROVE_PERMISSION
    context_object_name = 'photos'
    template_name = 'dashboard/ai_model_review.html'
    paginate_by = 24

    def get_queryset(self):
        # Mais antigas primeiro: quem enviou antes é revisado antes
        return (
            TelegramPhoto.objects.awaiting_approval()
            .select_related('telegram_user__profile__user')
            .order_by('received_at', 'pk')
        )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['link'] = 'ai-model-review'
        data['approved_total'] = TelegramPhoto.objects.approved().count()
        data['rejected_total'] = TelegramPhoto.objects.rejected().count()
        data['awaiting_description_total'] = TelegramPhoto.objects.awaiting_description().count()

        # Opções dos selects. O template filtra doença pela planta e estado pela
        # doença no navegador, a partir de catalog (json_script).
        data['cultures'] = Culture.objects.all()
        data['catalog'] = {
            'diseases': [
                {'id': d.pk, 'name': d.name_disease, 'culture': d.culture_disease_id, 'states': d.states}
                for d in Disease.objects.order_by('name_disease')
            ],
        }
        return data


@login_required
@permission_required(APPROVE_PERMISSION, raise_exception=True)
def ai_model_photo_file(request, pk):
    """Entrega a imagem de media-ia/, que não tem URL pública, a quem revisa"""

    photo = get_object_or_404(TelegramPhoto, pk=pk, purpose=TelegramPhoto.PURPOSE_TRAINING)
    if not photo.image:
        raise Http404("Imagem ainda não baixada")

    return FileResponse(photo.image.open('rb'))


# POST e não GET, ao contrário dos accept_* antigos: aprovar e reprovar mudam
# estado, e um GET pode ser disparado por pré-carregamento de link.
@require_POST
@login_required
@permission_required(APPROVE_PERMISSION, raise_exception=True)
def ai_model_photo_approve(request, pk):
    form = AIModelApprovalForm(request.POST)

    if not form.is_valid():
        erros = [e for lista in form.errors.values() for e in lista]
        messages.error(request, "Imagem #{} não aprovada: {}".format(pk, " ".join(erros)))
        return redirect('dashboard:ai_model_review')

    try:
        # Um estado novo só fica gravado se a aprovação der certo
        with transaction.atomic():
            state = form.get_state()
            photo = approve_training_photo(pk, request.user, form.cleaned_data['disease'], state)
        messages.success(request, "Imagem #{} aprovada e salva no treino como {}.".format(
            pk, photo.image.name.rsplit('/', 1)[-1]))
    except TelegramPhoto.DoesNotExist:
        messages.warning(request, "A imagem #{} já foi revisada.".format(pk))
    except ValueError as e:
        messages.error(request, "Imagem #{} não aprovada: {}".format(pk, e))

    return redirect('dashboard:ai_model_review')


@require_POST
@login_required
@permission_required(APPROVE_PERMISSION, raise_exception=True)
def ai_model_photo_reject(request, pk):
    try:
        reject_training_photo(pk, request.user)
        messages.success(request, "Imagem #{} reprovada. O arquivo foi excluído e a decisão ficou registrada.".format(pk))
    except TelegramPhoto.DoesNotExist:
        messages.warning(request, "A imagem #{} já foi revisada.".format(pk))

    return redirect('dashboard:ai_model_review')
