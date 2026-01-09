"""Celery application configuration."""

from celery import Celery

from app.core.config import settings
from app.core.logger import logger # noqa

# Create Celery app with Redis broker
celery_app = Celery(
    "traceweaver",
    broker=settings.redis.url,
    backend=settings.redis.url,
    include=["app.workers.tasks"],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Worker settings
    worker_concurrency=settings.celery.worker_concurrency,
    worker_prefetch_multiplier=1,  # Prevent prefetching for better concurrency control
    # Task execution settings
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,  # Requeue task if worker crashes
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
)
