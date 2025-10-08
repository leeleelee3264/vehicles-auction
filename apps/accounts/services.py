from datetime import timedelta
from typing import Dict, Optional

from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class JWTService:
    """JWT 토큰 관리 서비스"""

    def create_tokens_for_user(self, user: User) -> Dict[str, str]:

        refresh = RefreshToken.for_user(user)

        access_token = refresh.access_token
        access_token['username'] = user.username
        access_token['is_staff'] = user.is_staff

        return {
            'access': str(access_token),
            'refresh': str(refresh)
        }


class AccountService:
    """계정 관련 비즈니스 로직 서비스"""

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        사용자 인증

        Args:
            username: 사용자명
            password: 비밀번호

        Returns:
            인증된 User 객체 또는 None
        """
        return authenticate(username=username, password=password)

    def can_approve_auction(self, user: User) -> bool:
        """
        사용자가 경매를 승인할 수 있는지 확인

        Args:
            user: 확인할 사용자

        Returns:
            경매 승인 가능 여부
        """
        return user.is_staff
