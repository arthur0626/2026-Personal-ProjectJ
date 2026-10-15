from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from kombu.exceptions import OperationalError

from activity.models import ActivityEvent
from common.models import ProcessingRun

from .models import CodeAnalysis, CodingSubmission
from .tasks import analyze_submission

SOURCE = 'def solve():\n\tif a < b:\n\t\treturn "<script>"   \n\n'


class CodingTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='owner', password='pw', is_staff=True)
        self.other = User.objects.create_user(username='other', password='pw', is_staff=True)

    def record(self, user=None, **fields):
        fields = {
            'platform': 'programmers', 'problem_title': '두 수의 합', 'language': 'python',
            'source_code': SOURCE, 'submitted_at': timezone.now(), **fields,
        }
        return CodingSubmission.record(user=user or self.owner, **fields)


class RecordTests(CodingTestCase):
    def test_submission_is_represented_by_activity_event(self):
        submission = self.record()
        event = submission.activity_event
        self.assertEqual(
            (event.user, event.event_type, event.source, event.occurred_at, event.visibility),
            (self.owner, 'coding_submission', 'manual', submission.submitted_at, 'private'),
        )
        self.assertEqual(event.coding_submission, submission)

    def test_same_commit_file_cannot_be_ingested_twice(self):
        commit = {'repository': 'me/algo', 'commit_sha': 'a' * 40, 'file_path': 'p/1.py'}
        self.record(source='github', **commit)
        with self.assertRaises(IntegrityError):
            self.record(source='github', **commit)
        # The failed attempt rolled back its ActivityEvent too.
        self.assertEqual(ActivityEvent.objects.count(), 1)

    def test_manual_entries_without_commit_may_repeat(self):
        self.record()
        self.record()
        self.assertEqual(CodingSubmission.objects.count(), 2)


class ViewTests(CodingTestCase):
    def test_owner_records_submission_with_source_verbatim(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('coding:new'), {
            'platform': 'swea', 'problem_title': 'T', 'language': 'python',
            'submitted_at': '2026-10-14T12:30', 'source_code': SOURCE,
        })
        submission = CodingSubmission.objects.get()
        self.assertRedirects(response, reverse('coding:detail', args=[submission.pk]))
        self.assertEqual(submission.source_code, SOURCE)
        self.assertEqual(submission.ingestion_status, 'ingested')
        page = self.client.get(reverse('coding:detail', args=[submission.pk]))
        self.assertContains(page, '&quot;&lt;script&gt;&quot;')
        self.assertNotContains(page, '"<script>"')

    def test_views_are_owner_only(self):
        submission = self.record()
        guest = get_user_model().objects.create_user(username='guest')
        urls = [reverse('coding:index'), reverse('coding:new'),
                reverse('coding:detail', args=[submission.pk]), reverse('activity:timeline')]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 302, url)
        self.client.force_login(guest)
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_other_owner_cannot_see_submission(self):
        submission = self.record()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('coding:detail', args=[submission.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse('coding:index')), '두 수의 합')

    def test_analysis_is_labelled_as_reviewable(self):
        submission = self.record()
        CodeAnalysis.objects.create(submission=submission, status='succeeded',
                                    summary='해시맵 풀이', key_concepts=['hash'])
        self.client.force_login(self.owner)
        page = self.client.get(reverse('coding:detail', args=[submission.pk]))
        self.assertContains(page, '검토가 필요합니다')
        self.assertContains(page, '해시맵 풀이')


class TimelineTests(CodingTestCase):
    def test_timeline_lists_own_events_newest_first(self):
        now = timezone.now()
        self.record(problem_title='OLDER-ONE', submitted_at=now - timedelta(days=1))
        self.record(problem_title='NEWER-ONE', submitted_at=now)
        self.record(user=self.other, problem_title='someone-else', submitted_at=now)
        self.client.force_login(self.owner)
        page = self.client.get(reverse('activity:timeline')).content.decode()
        self.assertLess(page.index('NEWER-ONE'), page.index('OLDER-ONE'))
        self.assertNotIn('someone-else', page)


@mock.patch('coding.views.analyze_submission.delay')
class AnalysisRequestTests(CodingTestCase):
    def setUp(self):
        super().setUp()
        self.submission = self.record()
        self.url = reverse('coding:request_analysis', args=[self.submission.pk])

    def test_request_enqueues_and_returns_without_running_the_task(self, delay):
        self.client.force_login(self.owner)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('coding:detail', args=[self.submission.pk]))
        run = ProcessingRun.objects.get()
        delay.assert_called_once_with(run.pk)
        self.assertEqual((run.status, run.attempts, run.related_object), ('queued', 0, self.submission))
        self.assertContains(self.client.get(response.url), '시도 0회')

    def test_any_enqueue_failure_marks_run_failed(self, delay):
        self.client.force_login(self.owner)
        for error in (OperationalError('connection refused'), ConnectionError('reset')):
            delay.side_effect = error
            with self.assertLogs('coding.views', 'ERROR'):
                response = self.client.post(self.url)
            self.assertEqual(response.status_code, 302)
        self.assertEqual(
            list(ProcessingRun.objects.values_list('status', flat=True)), ['failed', 'failed']
        )
        self.assertIn('Enqueue failed: ConnectionError', ProcessingRun.objects.first().error_summary)

    def test_only_owner_may_post(self, delay):
        self.assertEqual(self.client.post(self.url).status_code, 302)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.url).status_code, 404)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        delay.assert_not_called()


class AnalyzeTaskTests(CodingTestCase):
    def run_for(self, submission):
        return ProcessingRun.objects.create(
            user=self.owner, run_type='coding.analyze', related_object=submission
        )

    @override_settings(LLM_PROVIDER='')
    def test_failure_is_recorded_and_reraised(self):
        run = self.run_for(self.record())
        with self.assertLogs('common.models', 'ERROR'), self.assertRaises(ImproperlyConfigured):
            analyze_submission(run.pk)
        run.refresh_from_db()
        self.assertEqual((run.status, run.attempts), ('failed', 1))
        self.assertIn('LLM provider is not configured', run.error_summary)
        self.assertIsNotNone(run.finished_at)

    @override_settings(LLM_PROVIDER='mock')
    def test_success_is_recorded_and_retry_counts_attempts(self):
        run = self.run_for(self.record())
        analyze_submission(run.pk)
        analyze_submission(run.pk)
        run.refresh_from_db()
        self.assertEqual((run.status, run.attempts, run.error_summary), ('succeeded', 2, ''))
