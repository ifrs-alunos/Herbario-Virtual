# Reexporta o form de accounts em vez de manter uma cópia.
# dashboard.views.accounts.create_user usava esta cópia enquanto importava o
# ProfileForm de accounts, então uma validação adicionada só lá não teria efeito
# no cadastro. Uma classe só, uma fonte de verdade.
from accounts.forms.user_form import UserForm  # noqa: F401
