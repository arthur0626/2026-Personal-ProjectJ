from django.conf import settings
from django.db import models
from django.utils import timezone


class BlogPostQuerySet(models.QuerySet):
    def public(self):
        """The only queryset public routes may read from."""
        return self.filter(
            status=BlogPost.Status.PUBLISHED,
            visibility=BlogPost.Visibility.PUBLIC,
        )


class BlogPost(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', '초안'
        PUBLISHED = 'published', '발행됨'

    class Visibility(models.TextChoices):
        PUBLIC = 'public', '공개'
        PRIVATE = 'private', '비공개'

    # PROTECT: posts must not vanish with a User until the withdrawal policy is decided.
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='blog_posts'
    )
    title = models.CharField('제목', max_length=200)
    slug = models.SlugField('slug', unique=True)
    excerpt = models.TextField('요약', blank=True)
    body = models.TextField('본문')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    visibility = models.CharField(
        '공개 범위', max_length=20, choices=Visibility.choices, default=Visibility.PUBLIC
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    objects = BlogPostQuerySet.as_manager()

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    def publish(self):
        self.status = self.Status.PUBLISHED
        self.published_at = self.published_at or timezone.now()
        self.save()

    def unpublish(self):
        self.status = self.Status.DRAFT
        self.published_at = None
        self.save()
