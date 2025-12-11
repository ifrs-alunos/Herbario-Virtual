try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    print("Aviso: Celery não está configurado. Continuando sem Celery...")
    celery_app = None

__all__ = ('celery_app',)