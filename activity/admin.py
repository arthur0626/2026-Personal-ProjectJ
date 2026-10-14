from django.contrib import admin

from .models import ActivityEvent


@admin.register(ActivityEvent)
class ActivityEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'source', 'user', 'occurred_at', 'processing_status')
    list_filter = ('event_type', 'source', 'processing_status')
