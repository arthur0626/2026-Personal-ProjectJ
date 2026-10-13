from django import forms
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm

from .models import User


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class AddPasswordForm(SetPasswordForm):
    """Allow a social-only user to establish a native login password."""

    new_password1 = forms.CharField(
        label='새 비밀번호',
        widget=forms.PasswordInput,
        strip=False,
    )
    new_password2 = forms.CharField(
        label='새 비밀번호 확인',
        widget=forms.PasswordInput,
        strip=False,
    )
