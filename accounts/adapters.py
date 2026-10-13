"""개인정보 최소 수집을 위한 django-allauth 확장 지점."""

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class PrivacyFirstSocialAccountAdapter(DefaultSocialAccountAdapter):
    """카카오 식별자 외 프로필·연락처 정보를 사용자 DB에 저장하지 않는다."""

    def populate_user(self, request, sociallogin, data):
        # allauth 기본 구현은 제공자의 이메일·닉네임·이름을 User에 채운다.
        # 이 서비스는 사용자 입력이나 해당 프로필 정보를 수집하지 않는다.
        user = sociallogin.user
        user.username = ''
        user.email = ''
        user.first_name = ''
        user.last_name = ''
        return user

    def pre_social_login(self, request, sociallogin):
        # SocialAccount에는 OAuth provider와 UID만 남긴다. 카카오 응답 원문
        # (닉네임·이메일 등)은 저장하지 않아 추후 동의 기반 프로필 기능과 분리한다.
        sociallogin.account.extra_data = {}
        sociallogin.email_addresses = []
