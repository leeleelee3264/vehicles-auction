from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class TestUserModel(TestCase):
    """User 모델 테스트"""

    def test_create_user_success(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_without_username(self):
        with self.assertRaises(TypeError):
            User.objects.create_user(
                email='test@example.com',
                password='testpass123'
            )

    def test_username_unique_constraint(self):
        User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='testuser',
                password='differentpass'
            )

    def test_password_hashing(self):
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # 비밀번호가 평문으로 저장되지 않음
        self.assertNotEqual(user.password, 'testpass123')
        # 해시된 비밀번호 확인
        self.assertTrue(user.password.startswith('pbkdf2_sha256'))
