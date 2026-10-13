from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from allauth.socialaccount.internal.flows.connect import validate_disconnect
from allauth.socialaccount.models import SocialAccount


class NativeAuthenticationTests(TestCase):
    def test_home_is_public(self):
        response = self.client.get(reverse('accounts:home'))
        self.assertEqual(response.status_code, 200)

    def test_registration_creates_user_and_redirects_to_login(self):
        response = self.client.post(reverse('auth:register'), {
            'username': 'owner',
            'email': 'owner@example.com',
            'password1': 'safe-test-password-123',
            'password2': 'safe-test-password-123',
        })
        self.assertRedirects(response, reverse('auth:login'))
        self.assertTrue(get_user_model().objects.filter(username='owner').exists())

    def test_login_creates_session_and_redirects_to_dashboard(self):
        get_user_model().objects.create_user(
            username='owner', password='safe-test-password-123'
        )
        response = self.client.post(reverse('auth:login'), {
            'username': 'owner',
            'password': 'safe-test-password-123',
        })
        self.assertRedirects(response, reverse('accounts:dashboard'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertRedirects(response, '/accounts/login/?next=/dashboard/')

    def test_logout_ends_session(self):
        user = get_user_model().objects.create_user(
            username='owner', password='safe-test-password-123'
        )
        self.client.force_login(user)
        response = self.client.post(reverse('auth:logout'))
        self.assertRedirects(response, reverse('accounts:home'))
        dashboard_response = self.client.get(reverse('accounts:dashboard'))
        self.assertRedirects(
            dashboard_response,
            '/accounts/login/?next=/dashboard/',
        )

    def test_account_settings_requires_login(self):
        response = self.client.get(reverse('auth:settings'))
        self.assertRedirects(
            response,
            '/accounts/login/?next=/accounts/settings/',
        )


class KakaoLinkingTests(TestCase):
    def test_login_page_exposes_kakao_login_entrypoint(self):
        response = self.client.get(reverse('auth:login'))

        self.assertContains(response, '/accounts/social/kakao/login/')

    def test_kakao_connect_requires_login(self):
        response = self.client.get(reverse('auth:kakao_connect'))
        self.assertRedirects(
            response,
            '/accounts/login/?next=/accounts/kakao/connect/',
        )

    def test_kakao_connect_starts_explicit_connect_flow(self):
        user = get_user_model().objects.create_user(
            username='owner', password='safe-test-password-123'
        )
        self.client.force_login(user)

        response = self.client.get(reverse('auth:kakao_connect'))

        self.assertRedirects(
            response,
            '/accounts/social/kakao/login/?process=connect',
            fetch_redirect_response=False,
        )

    def test_social_profile_data_is_not_copied_to_user_or_account(self):
        from types import SimpleNamespace

        from .adapters import PrivacyFirstSocialAccountAdapter

        user = get_user_model()()
        sociallogin = SimpleNamespace(
            user=user,
            account=SimpleNamespace(extra_data={
                'id': 123,
                'properties': {'nickname': 'private nickname'},
            }),
            email_addresses=[SimpleNamespace(email='private@example.com')],
        )
        adapter = PrivacyFirstSocialAccountAdapter()

        adapter.populate_user(None, sociallogin, {
            'username': 'kakao-name',
            'email': 'private@example.com',
            'first_name': 'Private',
        })
        adapter.pre_social_login(None, sociallogin)

        self.assertEqual(user.username, '')
        self.assertEqual(user.email, '')
        self.assertEqual(user.first_name, '')
        self.assertEqual(sociallogin.account.extra_data, {})
        self.assertEqual(sociallogin.email_addresses, [])

    def test_social_only_user_can_add_native_password(self):
        user = get_user_model().objects.create_user(username='social-owner')
        user.set_unusable_password()
        user.save(update_fields=['password'])
        self.client.force_login(user)

        response = self.client.post(reverse('auth:settings'), {
            'new_password1': 'safe-test-password-123',
            'new_password2': 'safe-test-password-123',
        })

        self.assertRedirects(response, reverse('auth:settings'))
        user.refresh_from_db()
        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.check_password('safe-test-password-123'))

    def test_social_only_user_cannot_disconnect_last_login_method(self):
        user = get_user_model().objects.create_user(username='social-owner')
        user.set_unusable_password()
        user.save(update_fields=['password'])
        account = SocialAccount.objects.create(
            user=user,
            provider='kakao',
            uid='mock-kakao-123',
            extra_data={},
        )

        with self.assertRaises(ValidationError):
            validate_disconnect(self.client.request().wsgi_request, account)
