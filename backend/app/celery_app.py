from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "rag",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
)
celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"])
