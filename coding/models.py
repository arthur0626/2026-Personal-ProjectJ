from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.db.models import Q

from activity.models import ActivityEvent
from common.models import ProcessingRun


class CodingSubmission(models.Model):
    class Platform(models.TextChoices):
        PROGRAMMERS = 'programmers', '프로그래머스'
        SWEA = 'swea', 'SWEA'
        BAEKJOON = 'baekjoon', '백준'
        LEETCODE = 'leetcode', 'LeetCode'
        OTHER = 'other', '기타'

    class IngestionStatus(models.TextChoices):
        PENDING = 'pending', '대기'
        INGESTED = 'ingested', '수집 완료'
        FAILED = 'failed', '실패'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='coding_submissions'
    )
    activity_event = models.OneToOneField(
        ActivityEvent, on_delete=models.PROTECT, related_name='coding_submission'
    )
    platform = models.CharField('플랫폼', max_length=20, choices=Platform.choices)
    problem_external_id = models.CharField('문제 번호', max_length=100, blank=True)
    problem_title = models.CharField('문제 제목', max_length=200)
    problem_url = models.URLField('문제 URL', blank=True)
    language = models.CharField('언어', max_length=40)
    # Canonical copy of the owner's code: stored verbatim, never rewritten.
    source_code = models.TextField('소스 코드')
    repository = models.CharField(max_length=200, blank=True)
    branch = models.CharField(max_length=200, blank=True)
    commit_sha = models.CharField(max_length=40, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    submitted_at = models.DateTimeField('제출 시각')
    ingestion_status = models.CharField(
        max_length=20, choices=IngestionStatus.choices, default=IngestionStatus.PENDING
    )
    processing_runs = GenericRelation(ProcessingRun)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']
        constraints = [
            # One file in one commit is one submission; manual entries have no commit.
            models.UniqueConstraint(
                fields=['repository', 'commit_sha', 'file_path'],
                condition=~Q(commit_sha=''),
                name='unique_submission_per_commit_file',
            ),
        ]

    def __str__(self):
        return f'[{self.get_platform_display()}] {self.problem_title}'

    @classmethod
    @transaction.atomic
    def record(cls, *, user, source=ActivityEvent.Source.MANUAL, **fields):
        """Create the submission together with the ActivityEvent that represents it."""
        event = ActivityEvent.objects.create(
            user=user,
            event_type=ActivityEvent.EventType.CODING_SUBMISSION,
            source=source,
            occurred_at=fields['submitted_at'],
        )
        return cls.objects.create(user=user, activity_event=event, **fields)


class CodeAnalysis(models.Model):
    """LLM output about a submission: reviewable generated content, not source of truth."""

    class Status(models.TextChoices):
        PENDING = 'pending', '대기'
        SUCCEEDED = 'succeeded', '완료'
        FAILED = 'failed', '실패'

    # Several rows per submission are allowed: retries and new prompt versions.
    submission = models.ForeignKey(
        CodingSubmission, on_delete=models.CASCADE, related_name='analyses'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    summary = models.TextField(blank=True)
    approach = models.TextField(blank=True)
    time_complexity = models.CharField(max_length=100, blank=True)
    space_complexity = models.CharField(max_length=100, blank=True)
    key_concepts = models.JSONField(default=list, blank=True)
    strengths = models.JSONField(default=list, blank=True)
    possible_improvements = models.JSONField(default=list, blank=True)
    pitfalls = models.JSONField(default=list, blank=True)
    raw_structured_output = models.JSONField(null=True, blank=True)
    model_provider = models.CharField(max_length=50, blank=True)
    model_name = models.CharField(max_length=100, blank=True)
    prompt_version = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Analysis of {self.submission} ({self.status})'
