from django.db import models
from .base import BaseModel

class MathModelRequirement(BaseModel):
    """Tabela intermediária para requisitos de modelos matemáticos"""
    math_model = models.ForeignKey(
        'MathModel',
        on_delete=models.CASCADE,
        related_name='mathmodel_requirements'
    )
    requirement = models.ForeignKey(
        'Requirement',
        on_delete=models.CASCADE,
        related_name='requirement_mathmodels'
    )
    is_required = models.BooleanField(
        "Obrigatório",
        default=True,
        help_text="Se desmarcado, este requisito é opcional"
    )
    order = models.PositiveIntegerField(
        "Ordem",
        default=0,
        help_text="Ordem de verificação dos requisitos"
    )

    class Meta:
        verbose_name = "Requisito do Modelo"
        verbose_name_plural = "Requisitos dos Modelos"
        ordering = ['order']
        unique_together = ('math_model', 'requirement')

    def __str__(self):
        return f"{self.math_model.name} - {self.requirement.name}"