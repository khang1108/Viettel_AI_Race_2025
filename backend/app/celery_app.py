from celery import Celery, signals
from app.core.config import settings

celery_app = Celery(
    "rag",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    worker_prefetch_multiplier=1,
    imports=["app.tasks"]
)

# Register worker init hook
from app.worker_init import init_worker
signals.worker_process_init.connect(init_worker)