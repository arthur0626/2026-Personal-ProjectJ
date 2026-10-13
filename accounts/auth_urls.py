from django.urls import path

from . import auth_views

app_name = 'auth'

urlpatterns = [
    path('register/', auth_views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutConfirmView.as_view(), name='logout'),
    path('settings/', auth_views.account_settings, name='settings'),
    path('kakao/connect/', auth_views.kakao_connect, name='kakao_connect'),
]
