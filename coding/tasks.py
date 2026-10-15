from celery import shared_task
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from common.models import ProcessingRun


@shared_task
def analyze_submission(run_id):
    run = ProcessingRun.objects.get(pk=run_id)
    with run.track():
        # Milestone 8 replaces this with the LLM client call after Checkpoint C.
        if not settings.LLM_PROVIDER:
            raise ImproperlyConfigured('LLM provider is not configured (Milestone 8).')
