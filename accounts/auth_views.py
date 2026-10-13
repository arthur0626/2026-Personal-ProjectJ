from django.contrib.auth import update_session_auth_hash, views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import urlencode

from allauth.socialaccount.models import SocialAccount

from .forms import AddPasswordForm, RegistrationForm


class LoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True


class LogoutConfirmView(LogoutView):
    next_page = reverse_lazy('accounts:home')


def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('auth:login')
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def account_settings(request):
    password_form = AddPasswordForm(request.user)
    if request.method == 'POST':
        password_form = AddPasswordForm(request.user, request.POST)
        if password_form.is_valid():
            password_form.save()
            update_session_auth_hash(request, request.user)
            return redirect('auth:settings')

    return render(request, 'accounts/settings.html', {
        'password_form': password_form,
        'social_accounts': SocialAccount.objects.filter(user=request.user),
    })


@login_required
def kakao_connect(request):
    """Start an explicit Kakao account-linking flow for the current user."""
    query = urlencode({'process': 'connect'})
    return redirect(f'{reverse("kakao_login")}?{query}')
