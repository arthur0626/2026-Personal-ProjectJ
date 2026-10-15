import logging
from contextlib import contextmanager

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class ProcessingRun(models.Model):
    """Product-level record of one background job; Celery keeps its own internals."""

    class Status(models.TextChoices):
        QUEUED = 'queued', '대기'
        RUNNING = 'running', '실행 중'
        SUCCEEDED = 'succeeded', '완료'
        FAILED = 'failed', '실패'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='processing_runs'
    )
    run_type = models.CharField(max_length=50)
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, null=True, blank=True)
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    attempts = models.PositiveSmallIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error_summary = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['content_type', 'object_id'])]

    def __str__(self):
        return f'{self.run_type} #{self.pk} ({self.status})'

    @contextmanager
    def track(self):
        """Wrap one task attempt: record start, then success or failure, and re-raise errors."""
        self.status, self.started_at, self.finished_at = self.Status.RUNNING, timezone.now(), None
        self.attempts += 1
        self.save()
        try:
            yield self
        except Exception as exc:
            self.fail(f'{type(exc).__name__}: {exc}')
            logger.exception('ProcessingRun %s failed', self.pk)
            raise
        self.status, self.finished_at = self.Status.SUCCEEDED, timezone.now()
        self.save()

    def fail(self, summary):
        self.status, self.finished_at, self.error_summary = (
            self.Status.FAILED, timezone.now(), summary[:1000]
        )
        self.save()
