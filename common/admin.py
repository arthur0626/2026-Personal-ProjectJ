from django.contrib import admin

from .models import ProcessingRun


@admin.register(ProcessingRun)
class ProcessingRunAdmin(admin.ModelAdmin):
    list_display = ('run_type', 'status', 'attempts', 'user', 'created_at', 'finished_at')
    list_filter = ('run_type', 'status')
