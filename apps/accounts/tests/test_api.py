from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class TestAuthenticationAPI(TestCase):
    """인증 API 테스트"""
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_login_success(self):
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


    def test_access_protected_endpoint_without_token(self):
        response = self.client.get('/api/vehicles/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_protected_endpoint_with_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/vehicles/')

        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_with_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token_here')
        response = self.client.get('/api/vehicles/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_with_expired_token(self):
        # 이미 만료된 토큰 (테스트용)
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjA5NDU5MjAwLCJqdGkiOiIxMjM0NTY3ODkwIiwidXNlcl9pZCI6MX0.test"

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')
        response = self.client.get('/api/vehicles/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestLoginResponseFormat(TestCase):
    """로그인 응답 형식 테스트"""

    def setUp(self):
        self.client = APIClient()

    def test_login_response_structure(self):
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

        if 'is_staff' in data['user']:
            self.assertTrue(data['user']['is_staff'])