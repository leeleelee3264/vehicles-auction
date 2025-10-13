from datetime import timedelta
from typing import Dict, Optional

from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.dto import LoginDTO

User = get_user_model()


class JWTService:

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

    def authenticate_user(self, login_data: LoginDTO) -> Optional[User]:
        return authenticate(username=login_data.username, password=login_data.password)

    # TODO: 경매할 때 쓰려나? 도메인 연관 관계를 어떻게 가져가야 할지 생각하기... 없다면 아예 JWTService 통합 -> Account로 통합하기
    # TODO: 이거 통합하면 View도 생각해봐야 함
    def can_approve_auction(self, user: User) -> bool:
        return user.is_staff
