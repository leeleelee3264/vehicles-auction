from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    차량 경매 시스템 사용자 모델
    Django 기본 User 모델을 상속받아 사용

    기본 제공 필드:
    - username: 로그인 ID
    - password: 비밀번호
    - email: 이메일
    - is_staff: 관리자 여부 (경매 승인 권한에 사용)
    - is_active: 계정 활성화 여부
    - is_superuser: 최고 관리자 여부
    - date_joined: 가입일
    - last_login: 마지막 로그인
    """

    class Meta:
        db_table = 'users'
        verbose_name = '사용자'
        verbose_name_plural = '사용자'