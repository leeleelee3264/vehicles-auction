from datetime import timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from freezegun import freeze_time
import jwt
from django.conf import settings

from apps.accounts.dto import LoginDTO

User = get_user_model()


class TestJWTService(TestCase):
    """JWT 토큰 관리 서비스 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_tokens_for_user(self):
        from apps.accounts.services import JWTService

        jwt_service = JWTService()
        tokens = jwt_service.create_tokens_for_user(self.user)

        self.assertIn('access', tokens)
        self.assertIn('refresh', tokens)
        self.assertIsInstance(tokens['access'], str)
        self.assertIsInstance(tokens['refresh'], str)
        self.assertGreater(len(tokens['access']), 0)
        self.assertGreater(len(tokens['refresh']), 0)

    def test_access_token_contains_user_info(self):
        from apps.accounts.services import JWTService

        jwt_service = JWTService()
        tokens = jwt_service.create_tokens_for_user(self.user)

        # JWT 디코드 (서명 검증 없이)
        decoded = jwt.decode(
            tokens['access'],
            options={"verify_signature": False}
        )

        self.assertIn('user_id', decoded)
        self.assertEqual(decoded['user_id'], self.user.id)
        self.assertIn('username', decoded)
        self.assertEqual(decoded['username'], self.user.username)

    def test_token_expiration_times(self):
        from apps.accounts.services import JWTService

        with freeze_time("2024-01-01 12:00:00"):
            jwt_service = JWTService()
            tokens = jwt_service.create_tokens_for_user(self.user)

            # Access token 디코드
            access_decoded = jwt.decode(
                tokens['access'],
                options={"verify_signature": False}
            )

            # Refresh token 디코드
            refresh_decoded = jwt.decode(
                tokens['refresh'],
                options={"verify_signature": False}
            )

            # 만료 시간 확인 (Unix timestamp)
            now_timestamp = timezone.now().timestamp()

            # Access token: 30분 후 만료
            access_exp_diff = access_decoded['exp'] - now_timestamp
            self.assertGreater(access_exp_diff, 1790)  # 약 30분
            self.assertLess(access_exp_diff, 1810)

            # Refresh token: 7일 후 만료
            refresh_exp_diff = refresh_decoded['exp'] - now_timestamp
            self.assertGreater(refresh_exp_diff, 604700)  # 약 7일
            self.assertLess(refresh_exp_diff, 604900)

    def test_staff_user_token_contains_is_staff(self):
        from apps.accounts.services import JWTService

        staff_user = User.objects.create_user(
            username='staffuser',
            password='staffpass123',
            is_staff=True
        )

        jwt_service = JWTService()
        tokens = jwt_service.create_tokens_for_user(staff_user)

        decoded = jwt.decode(
            tokens['access'],
            options={"verify_signature": False}
        )

        self.assertIn('is_staff', decoded)
        self.assertTrue(decoded['is_staff'])


class TestAccountService(TestCase):
    """계정 관련 비즈니스 로직 테스트"""

    def setUp(self):
        """테스트용 사용자 생성"""
        self.regular_user = User.objects.create_user(
            username='regular',
            password='pass123'
        )

        self.staff_user = User.objects.create_user(
            username='staff',
            password='pass123',
            is_staff=True
        )



    #TODO: 지워야 할 수 있다.
    def test_can_approve_auction_regular_user(self):
        """일반 사용자는 경매 승인 불가"""
        from apps.accounts.services import AccountService

        account_service = AccountService()
        self.assertFalse(account_service.can_approve_auction(self.regular_user))

    # TODO: 지워야 할 수 있다.
    def test_can_approve_auction_staff_user(self):
        """관리자는 경매 승인 가능"""
        from apps.accounts.services import AccountService

        account_service = AccountService()
        self.assertTrue(account_service.can_approve_auction(self.staff_user))

    def test_authenticate_user_success(self):
        from apps.accounts.services import AccountService

        User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        account_service = AccountService()
        user = account_service.authenticate_user(LoginDTO('testuser', 'testpass123'))

        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')

    def test_authenticate_user_wrong_password(self):
        from apps.accounts.services import AccountService

        User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        account_service = AccountService()
        user = account_service.authenticate_user(LoginDTO('testuser', 'wrongpass'))

        self.assertIsNone(user)

    def test_authenticate_user_nonexistent(self):
        from apps.accounts.services import AccountService

        account_service = AccountService()
        user = account_service.authenticate_user(LoginDTO('nonexistent', 'anypass'))

        self.assertIsNone(user)