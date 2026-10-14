from django import forms
from django.contrib.auth.hashers import make_password

from .models import BlogPost, Comment

# Single-segment routes in blog/urls.py that a post slug would shadow.
RESERVED_SLUGS = {'drafts', 'uploads'}


class BlogPostForm(forms.ModelForm):
    """Owner-editable fields; status changes only through publish/unpublish."""

    class Meta:
        model = BlogPost
        fields = ('title', 'slug', 'excerpt', 'body', 'visibility')

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        if slug in RESERVED_SLUGS:
            raise forms.ValidationError('사용할 수 없는 slug입니다.')
        return slug


class UploadForm(forms.Form):
    file = forms.FileField()


class CommentForm(forms.ModelForm):
    """Members comment as themselves; guests give a nickname and a delete password."""

    # Honeypot: hidden in the template, so only bots fill it.
    website = forms.CharField(required=False)

    class Meta:
        model = Comment
        fields = ('nickname', 'password', 'body')
        widgets = {'password': forms.PasswordInput, 'body': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user.is_authenticated:
            del self.fields['nickname'], self.fields['password']
        else:
            self.fields['password'].required = True

    def clean_website(self):
        if self.cleaned_data['website']:
            raise forms.ValidationError('잘못된 요청입니다.')
        return ''

    def save(self, commit=True):
        comment = super().save(commit=False)
        if self.user.is_authenticated:
            comment.user, comment.nickname = self.user, self.user.get_username()
        else:
            comment.password = make_password(self.cleaned_data['password'])
        if commit:
            comment.save()
        return comment
