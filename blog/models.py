from io import BytesIO
from pathlib import Path

import nh3
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from django.utils import timezone
from PIL import Image, ImageOps

ALIGN_CLASSES = {'ql-align-center', 'ql-align-right', 'ql-align-justify'}
BODY_TAGS = {
    'p', 'br', 'strong', 'em', 'u', 's', 'h1', 'h2', 'h3', 'blockquote',
    'pre', 'code', 'ol', 'ul', 'li', 'a', 'img',
}


def clean_body(html):
    """Allowlist sanitizer for editor HTML; the only gate before |safe output."""
    return nh3.clean(
        html,
        tags=BODY_TAGS,
        attributes={'a': {'href'}, 'img': {'src', 'alt'}},
        allowed_classes={tag: ALIGN_CLASSES for tag in ('p', 'h1', 'h2', 'h3', 'li', 'blockquote')},
    )


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

    def get_absolute_url(self):
        return reverse('blog:detail', args=[self.slug])

    def save(self, *args, **kwargs):
        # Sanitize here so forms, admin and future generated drafts share one gate.
        self.body = clean_body(self.body)
        super().save(*args, **kwargs)

    @property
    def is_public(self):
        return self.status == self.Status.PUBLISHED and self.visibility == self.Visibility.PUBLIC

    def publish(self):
        self.status = self.Status.PUBLISHED
        self.published_at = self.published_at or timezone.now()
        self.save()

    def unpublish(self):
        self.status = self.Status.DRAFT
        self.published_at = None
        self.save()


MAX_UPLOAD_SIZE = 10 * 1024 * 1024
IMAGE_EXTENSIONS = {'JPEG': 'jpg', 'PNG': 'png', 'GIF': 'gif', 'WEBP': 'webp'}
# No html/svg/js: uploads are served from the site origin and must not run script.
FILE_EXTENSIONS = {
    'pdf', 'txt', 'md', 'csv', 'json', 'zip', 'py', 'java', 'c', 'cpp', 'kt',
    'docx', 'xlsx', 'pptx', 'hwp',
}


class Attachment(models.Model):
    # shortcut: uploads are not linked to posts, so removed images stay on disk;
    # add an orphan cleanup when storage is planned in Milestone 11.
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='blog_attachments'
    )
    file = models.FileField(upload_to='blog/%Y/%m/')
    name = models.CharField(max_length=255)
    is_image = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @classmethod
    def from_upload(cls, upload, user):
        """Validate an uploaded file; images are re-encoded to drop EXIF/GPS data."""
        if upload.size > MAX_UPLOAD_SIZE:
            raise ValidationError('파일은 10MB 이하만 올릴 수 있습니다.')
        name = Path(upload.name).name
        ext = Path(name).suffix.lower().lstrip('.')
        if ext in {'jpg', 'jpeg', 'png', 'gif', 'webp'}:
            fmt, content = cls._reencode_image(upload)
            name = f'{Path(name).stem}.{IMAGE_EXTENSIONS[fmt]}'
            data = ContentFile(content, name=name)
            is_image = True
        elif ext in FILE_EXTENSIONS:
            data, is_image = upload, False
        else:
            raise ValidationError('허용되지 않는 파일 형식입니다.')
        attachment = cls(uploaded_by=user, name=name, is_image=is_image)
        attachment.file.save(name, data, save=True)
        return attachment

    @staticmethod
    def _reencode_image(upload):
        try:
            image = Image.open(upload)
            fmt = image.format
            if fmt not in IMAGE_EXTENSIONS:
                raise ValidationError('지원하지 않는 이미지 형식입니다.')
            animated = getattr(image, 'is_animated', False)
            if not animated:
                # Apply the camera rotation before the EXIF that stores it is dropped.
                image = ImageOps.exif_transpose(image)
            buffer = BytesIO()
            image.save(buffer, format=fmt, save_all=animated)
        except ValidationError:
            raise
        except (OSError, ValueError, SyntaxError, Image.DecompressionBombError):
            raise ValidationError('이미지 파일을 읽을 수 없습니다.')
        return fmt, buffer.getvalue()


class Comment(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    # Null for guest comments; PROTECT until the withdrawal policy is decided.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='blog_comments',
    )
    nickname = models.CharField('닉네임', max_length=20)
    password = models.CharField('비밀번호', max_length=128, blank=True)
    body = models.TextField('댓글', max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.nickname}: {self.body[:30]}'

    @property
    def is_guest(self):
        return self.user_id is None

    def can_delete(self, user, password=''):
        if user.is_authenticated and (user.is_staff or user.pk == self.user_id):
            return True
        return self.is_guest and bool(password) and check_password(password, self.password)
