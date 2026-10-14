from django import forms

from .models import CodingSubmission


class SubmissionForm(forms.ModelForm):
    # Django strips CharField input by default; source code must stay verbatim.
    source_code = forms.CharField(
        label='소스 코드', strip=False,
        widget=forms.Textarea(attrs={'rows': 20, 'spellcheck': 'false'}),
    )

    class Meta:
        model = CodingSubmission
        fields = (
            'platform', 'problem_external_id', 'problem_title', 'problem_url',
            'language', 'submitted_at', 'source_code',
        )
        widgets = {'submitted_at': forms.DateTimeInput(attrs={'type': 'datetime-local'})}
