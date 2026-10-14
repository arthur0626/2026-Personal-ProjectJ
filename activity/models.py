from django.conf import settings
from django.db import models


class ActivityEvent(models.Model):
    """The common fact "a meaningful activity happened"; details live in domain apps."""

    class EventType(models.TextChoices):
        CODING_SUBMISSION = 'coding_submission', '코딩 제출'

    class Source(models.TextChoices):
        MANUAL = 'manual', '직접 입력'
        GITHUB = 'github', 'GitHub'

    class Visibility(models.TextChoices):
        PRIVATE = 'private', '비공개'
        PUBLIC = 'public', '공개'

    class ProcessingStatus(models.TextChoices):
        PENDING = 'pending', '대기'
        PROCESSING = 'processing', '처리 중'
        DONE = 'done', '완료'
        FAILED = 'failed', '실패'

    # PROTECT: activity must not vanish with a User until the withdrawal policy is decided.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='activity_events'
    )
    event_type = models.CharField(max_length=40, choices=EventType.choices)
    source = models.CharField(max_length=20, choices=Source.choices)
    occurred_at = models.DateTimeField()
    visibility = models.CharField(
        max_length=20, choices=Visibility.choices, default=Visibility.PRIVATE
    )
    processing_status = models.CharField(
        max_length=20, choices=ProcessingStatus.choices, default=ProcessingStatus.PENDING
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-occurred_at']
        indexes = [models.Index(fields=['user', '-occurred_at'])]

    def __str__(self):
        return f'{self.get_event_type_display()} @ {self.occurred_at:%Y-%m-%d %H:%M}'
