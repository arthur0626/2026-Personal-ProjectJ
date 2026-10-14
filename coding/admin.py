from django.contrib import admin

from .models import CodeAnalysis, CodingSubmission


@admin.register(CodingSubmission)
class CodingSubmissionAdmin(admin.ModelAdmin):
    list_display = ('problem_title', 'platform', 'language', 'user', 'submitted_at', 'ingestion_status')
    list_filter = ('platform', 'ingestion_status')
    search_fields = ('problem_title', 'problem_external_id')
    raw_id_fields = ('activity_event',)


@admin.register(CodeAnalysis)
class CodeAnalysisAdmin(admin.ModelAdmin):
    list_display = ('submission', 'status', 'model_name', 'prompt_version', 'created_at')
    list_filter = ('status',)
