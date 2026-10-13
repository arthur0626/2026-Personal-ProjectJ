from django import forms

from .models import BlogPost


class BlogPostForm(forms.ModelForm):
    """Owner-editable fields; status changes only through publish/unpublish."""

    class Meta:
        model = BlogPost
        fields = ('title', 'slug', 'excerpt', 'body', 'visibility')

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        if slug == 'drafts':
            raise forms.ValidationError('사용할 수 없는 slug입니다.')
        return slug
