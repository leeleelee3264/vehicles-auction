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
