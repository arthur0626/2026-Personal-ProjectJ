from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from activity.models import ActivityEvent

from .models import CodeAnalysis, CodingSubmission

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
