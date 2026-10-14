from django.contrib import admin

from .models import Attachment, BlogPost, Comment


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'visibility', 'published_at')
    list_filter = ('status', 'visibility')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'nickname', 'user', 'created_at')
    exclude = ('password',)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_image', 'uploaded_by', 'created_at')
