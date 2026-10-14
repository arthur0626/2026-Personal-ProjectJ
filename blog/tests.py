import importlib
import shutil
import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .forms import BlogPostForm
from .models import Attachment, BlogPost, Comment


class BlogTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='owner', password='pw', is_staff=True)
        self.other = User.objects.create_user(username='other', password='pw', is_staff=True)

    def make_post(self, slug='post', **kwargs):
        kwargs.setdefault('author', self.owner)
        return BlogPost.objects.create(title=f'title-{slug}', slug=slug, body='body', **kwargs)


class PublicBoundaryTests(BlogTestCase):
    def test_draft_is_not_public(self):
        self.make_post('draft')
        self.assertNotContains(self.client.get(reverse('blog:index')), 'title-draft')
        self.assertEqual(self.client.get(reverse('blog:detail', args=['draft'])).status_code, 404)

    def test_published_private_post_is_not_public(self):
        self.make_post('secret', visibility=BlogPost.Visibility.PRIVATE).publish()
        self.assertNotContains(self.client.get(reverse('blog:index')), 'title-secret')
        self.assertEqual(self.client.get(reverse('blog:detail', args=['secret'])).status_code, 404)

    def test_published_public_post_is_visible(self):
        self.make_post('hello').publish()
        self.assertContains(self.client.get(reverse('blog:index')), 'title-hello')
        self.assertContains(self.client.get(reverse('blog:detail', args=['hello'])), 'title-hello')

    def test_only_author_can_preview_draft(self):
        self.make_post('draft')
        url = reverse('blog:detail', args=['draft'])
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(url).status_code, 200)


class DraftManagementTests(BlogTestCase):
    def test_management_requires_login(self):
        response = self.client.get(reverse('blog:drafts'))
        self.assertRedirects(response, '/accounts/login/?next=/blog/drafts/')

    def test_non_staff_user_cannot_author(self):
        self.client.force_login(get_user_model().objects.create_user(username='guest'))
        self.assertEqual(self.client.get(reverse('blog:drafts')).status_code, 403)
        self.assertEqual(self.client.post(reverse('blog:new'), {}).status_code, 403)

    def test_owner_creates_and_edits_draft(self):
        self.client.force_login(self.owner)
        data = {'title': 'T', 'slug': 'new-post', 'excerpt': '', 'body': 'B', 'visibility': 'public'}
        self.client.post(reverse('blog:new'), data)
        post = BlogPost.objects.get(slug='new-post')
        self.assertEqual((post.author, post.status, post.published_at),
                         (self.owner, BlogPost.Status.DRAFT, None))
        self.client.post(reverse('blog:edit', args=[post.pk]), {**data, 'title': 'T2'})
        post.refresh_from_db()
        self.assertEqual(post.title, 'T2')

    def test_drafts_list_shows_only_own_posts(self):
        self.make_post('mine')
        self.make_post('theirs', author=self.other)
        self.client.force_login(self.owner)
        response = self.client.get(reverse('blog:drafts'))
        self.assertContains(response, 'title-mine')
        self.assertNotContains(response, 'title-theirs')

    def test_other_user_cannot_edit_or_publish_by_guessed_id(self):
        post = self.make_post()
        self.client.force_login(self.other)
        for name in ('edit', 'publish', 'unpublish'):
            url = reverse(f'blog:{name}', args=[post.pk])
            self.assertEqual(self.client.post(url, {}).status_code, 404)
        post.refresh_from_db()
        self.assertEqual(post.status, BlogPost.Status.DRAFT)

    def test_publish_and_unpublish_set_state_and_time(self):
        post = self.make_post()
        self.client.force_login(self.owner)
        url = reverse('blog:publish', args=[post.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        post.refresh_from_db()
        self.assertEqual(post.status, BlogPost.Status.PUBLISHED)
        self.assertIsNotNone(post.published_at)
        self.client.post(reverse('blog:unpublish', args=[post.pk]))
        post.refresh_from_db()
        self.assertEqual((post.status, post.published_at), (BlogPost.Status.DRAFT, None))

    def test_slug_must_be_unique_and_not_reserved(self):
        self.make_post('taken')
        for slug in ('taken', 'drafts', 'uploads'):
            form = BlogPostForm({'title': 'T', 'slug': slug, 'body': 'B', 'visibility': 'public'})
            self.assertIn('slug', form.errors)


class BodySanitizeTests(BlogTestCase):
    def test_save_strips_script_handlers_and_dangerous_urls(self):
        post = self.make_post()
        post.body = (
            '<p class="ql-align-center evil" style="color:red" onclick="x()">hi</p>'
            '<script>alert(1)</script><a href="javascript:alert(1)">a</a>'
            '<img src="data:image/png;base64,AAAA" onerror="x()"><img src="/media/a.png">'
        )
        post.save()
        self.assertIn('<p class="ql-align-center">hi</p>', post.body)
        for bad in ('<script', 'onclick', 'onerror', 'style=', 'javascript:', 'data:', 'evil'):
            self.assertNotIn(bad, post.body)
        self.assertIn('<img src="/media/a.png">', post.body)

    def test_published_body_is_rendered_as_html(self):
        post = self.make_post('hello')
        post.body = '<p><strong>bold</strong></p>'
        post.publish()
        self.assertContains(self.client.get(reverse('blog:detail', args=['hello'])),
                            '<p><strong>bold</strong></p>', html=True)


class PlaintextMigrationTests(TestCase):
    def test_escapes_html_and_renders_code_blocks(self):
        migration = importlib.import_module('blog.migrations.0003_plaintext_body_to_html')
        html = migration.plaintext_to_html('intro <script>\n\n```python\nif a < b:\n    pass\n```\nafter')
        self.assertIn('<p>intro &lt;script&gt;</p>', html)
        self.assertIn('<pre><code>if a &lt; b:\n    pass\n</code></pre>', html)
        self.assertIn('<p>after</p>', html)
        self.assertNotIn('<script>', html)


class UploadTests(BlogTestCase):
    def setUp(self):
        super().setUp()
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media)
        settings = override_settings(MEDIA_ROOT=media)
        settings.enable()
        self.addCleanup(settings.disable)

    def upload(self, name, content):
        return self.client.post(reverse('blog:upload'), {'file': SimpleUploadedFile(name, content)})

    def jpeg_with_gps(self):
        exif = Image.Exif()
        exif[0x8825] = {2: (37.0, 30.0, 0.0)}  # GPSInfo latitude
        buffer = BytesIO()
        Image.new('RGB', (4, 4), 'red').save(buffer, 'JPEG', exif=exif)
        return buffer.getvalue()

    def test_non_staff_cannot_upload(self):
        self.client.force_login(get_user_model().objects.create_user(username='guest'))
        self.assertEqual(self.upload('a.txt', b'x').status_code, 403)
        self.assertFalse(Attachment.objects.exists())

    def test_image_is_reencoded_without_exif(self):
        self.client.force_login(self.owner)
        data = self.jpeg_with_gps()
        self.assertTrue(Image.open(BytesIO(data)).getexif())
        response = self.upload('photo.jpeg', data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_image'])
        attachment = Attachment.objects.get()
        with attachment.file.open('rb') as stored:
            self.assertFalse(Image.open(stored).getexif())

    def test_fake_image_and_script_files_are_rejected(self):
        self.client.force_login(self.owner)
        for name, content in (('x.png', b'<script>'), ('x.svg', b'<svg/>'), ('x.html', b'<p>')):
            self.assertEqual(self.upload(name, content).status_code, 400, name)
        self.assertFalse(Attachment.objects.exists())

    def test_allowed_file_is_stored(self):
        self.client.force_login(self.owner)
        response = self.upload('solution.py', b'print(1)')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name'], 'solution.py')
        self.assertFalse(response.json()['is_image'])


class CommentTests(BlogTestCase):
    def setUp(self):
        super().setUp()
        self.post = self.make_post('hello')
        self.post.publish()
        self.url = reverse('blog:comment_create', args=['hello'])

    def test_guest_comment_stores_hashed_password(self):
        self.client.post(self.url, {'nickname': 'ㅇㅇ', 'password': '1234', 'body': '안녕'})
        comment = Comment.objects.get()
        self.assertTrue(comment.is_guest)
        self.assertNotEqual(comment.password, '1234')
        self.assertTrue(check_password('1234', comment.password))
        self.assertContains(self.client.get(self.post.get_absolute_url()), '(비회원)')

    def test_guest_needs_nickname_and_password(self):
        response = self.client.post(self.url, {'body': '안녕'})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Comment.objects.exists())

    def test_member_comments_as_self(self):
        self.client.force_login(self.other)
        self.client.post(self.url, {'nickname': 'owner', 'body': 'hi'})
        comment = Comment.objects.get()
        self.assertEqual((comment.user, comment.nickname, comment.password), (self.other, 'other', ''))

    def test_honeypot_blocks_bots(self):
        self.client.post(self.url, {'nickname': 'bot', 'password': 'x', 'body': 'spam', 'website': 'x'})
        self.assertFalse(Comment.objects.exists())

    def test_no_comments_on_draft_or_private_posts(self):
        self.make_post('draft')
        self.make_post('secret', visibility=BlogPost.Visibility.PRIVATE).publish()
        for slug in ('draft', 'secret'):
            url = reverse('blog:comment_create', args=[slug])
            response = self.client.post(url, {'nickname': 'a', 'password': 'b', 'body': 'c'})
            self.assertEqual(response.status_code, 404)
        self.assertFalse(Comment.objects.exists())

    def test_guest_delete_requires_password(self):
        self.client.post(self.url, {'nickname': 'ㅇㅇ', 'password': '1234', 'body': '안녕'})
        delete = reverse('blog:comment_delete', args=[Comment.objects.get().pk])
        self.client.post(delete, {'password': 'wrong'})
        self.assertTrue(Comment.objects.exists())
        self.client.post(delete, {'password': '1234'})
        self.assertFalse(Comment.objects.exists())

    def test_member_cannot_delete_others_but_staff_can(self):
        guest = get_user_model().objects.create_user(username='guest')
        comment = Comment.objects.create(post=self.post, user=self.other, nickname='other', body='x')
        delete = reverse('blog:comment_delete', args=[comment.pk])
        self.client.force_login(guest)
        self.client.post(delete)
        self.assertTrue(Comment.objects.exists())
        self.client.force_login(self.owner)
        self.client.post(delete)
        self.assertFalse(Comment.objects.exists())
