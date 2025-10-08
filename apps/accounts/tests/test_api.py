from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest import skip
import json

User = get_user_model()


class TestAuthenticationAPI(TestCase):
    """인증 API 통합 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_login_success(self):
        """정상적인 로그인 성공"""
        response = self.client.post(
            '/api/auth/login/',
            data={
                'username': 'testuser',
                'password': 'testpass123'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('access', data)
        self.assertIn('refresh', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['id'], self.user.id)
        self.assertEqual(data['user']['username'], 'testuser')

    def test_login_wrong_password(self):
        """잘못된 비밀번호로 로그인 실패"""
        response = self.client.post(
            '/api/auth/login/',
            data={
                'username': 'testuser',
                'password': 'wrongpassword'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        self.assertNotIn('access', data)
        self.assertNotIn('refresh', data)

    def test_login_nonexistent_user(self):
        """존재하지 않는 사용자로 로그인 실패"""
        response = self.client.post(
            '/api/auth/login/',
            data={
                'username': 'nonexistent',
                'password': 'anypassword'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        self.assertNotIn('access', data)

    def test_login_missing_fields(self):
        """필수 필드 누락시 로그인 실패"""
        # username 누락
        response = self.client.post(
            '/api/auth/login/',
            data={'password': 'testpass123'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # password 누락
        response = self.client.post(
            '/api/auth/login/',
            data={'username': 'testuser'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_empty_fields(self):
        """빈 필드로 로그인 실패"""
        response = self.client.post(
            '/api/auth/login/',
            data={
                'username': '',
                'password': ''
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestProtectedEndpoints(TestCase):
    """인증이 필요한 엔드포인트 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # 로그인하여 토큰 획득
        response = self.client.post(
            '/api/auth/login/',
            data={
                'username': 'testuser',
                'password': 'testpass123'
            },
            format='json'
        )
        self.token = response.json()['access']

    @skip("Vehicle API not implemented yet")
    def test_access_protected_endpoint_without_token(self):
        """토큰 없이 보호된 엔드포인트 접근 차단"""
        response = self.client.get('/api/vehicles/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @skip("Vehicle API not implemented yet")
    def test_access_protected_endpoint_with_token(self):
        """토큰으로 보호된 엔드포인트 접근 허용"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/vehicles/')

        # 401이 아니면 인증 통과 (아직 vehicles API가 구현되지 않아 404일 수 있음)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @skip("Vehicle API not implemented yet")
    def test_access_with_invalid_token(self):
        """유효하지 않은 토큰으로 접근 차단"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token_here')
        response = self.client.get('/api/vehicles/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @skip("Vehicle API not implemented yet")
    def test_access_with_expired_token(self):
        """만료된 토큰으로 접근 차단"""
        # 이미 만료된 토큰 (테스트용)
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjA5NDU5MjAwLCJqdGkiOiIxMjM0NTY3ODkwIiwidXNlcl9pZCI6MX0.test"

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')
        response = self.client.get('/api/vehicles/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestLoginResponseFormat(TestCase):
    """로그인 응답 형식 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.client = APIClient()

    def test_login_response_structure(self):
        """로그인 응답 구조 검증"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        response = self.client.post(
            '/api/auth/login/',
            data={
                'username': 'testuser',
                'password': 'testpass123'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # 필수 필드 확인
        self.assertIn('access', data)
        self.assertIn('refresh', data)
        self.assertIn('user', data)

        # 토큰 형식 확인 (JWT는 3부분으로 구성)
        self.assertEqual(len(data['access'].split('.')), 3)
        self.assertEqual(len(data['refresh'].split('.')), 3)

        # 사용자 정보 확인
        self.assertEqual(data['user']['id'], user.id)
        self.assertEqual(data['user']['username'], 'testuser')
        # 민감한 정보는 포함되지 않아야 함
        self.assertNotIn('password', data['user'])

    def test_staff_user_login_response(self):
        """관리자 사용자 로그인 응답"""
        staff_user = User.objects.create_user(
            username='staffuser',
            password='staffpass123',
            is_staff=True
        )

        response = self.client.post(
            '/api/auth/login/',
            data={
                'username': 'staffuser',
                'password': 'staffpass123'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # 관리자 여부가 응답에 포함될 수 있음
        if 'is_staff' in data['user']:
            self.assertTrue(data['user']['is_staff'])