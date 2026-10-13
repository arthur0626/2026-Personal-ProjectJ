from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import BlogPostForm
from .models import BlogPost
from .templatetags.blog_extras import render_body


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
        for slug in ('taken', 'drafts'):
            form = BlogPostForm({'title': 'T', 'slug': slug, 'body': 'B', 'visibility': 'public'})
            self.assertIn('slug', form.errors)


class RenderBodyTests(TestCase):
    def test_escapes_html_and_renders_code_blocks(self):
        html = render_body('intro <script>\n\n```python\nif a < b:\n    pass\n```\nafter')
        self.assertIn('<p>intro &lt;script&gt;</p>', html)
        self.assertIn('<pre><code>if a &lt; b:\n    pass\n</code></pre>', html)
        self.assertIn('<p>after</p>', html)
        self.assertNotIn('<script>', html)
