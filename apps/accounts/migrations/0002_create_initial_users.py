from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_initial_users(apps, schema_editor):
    """초기 운영용 사용자 계정 생성"""
    User = apps.get_model('accounts', 'User')

    # 관리자 계정 생성 (운영용)
    User.objects.create(
        username='admin',
        email='admin@auction.com',
        password=make_password('admin123!@#'),
        is_staff=True,
        is_superuser=True,
        is_active=True
    )

    # 일반 사용자 계정 생성 (데모/테스트용)
    User.objects.create(
        username='demo_user',
        email='demo@auction.com',
        password=make_password('demo123!@#'),
        is_staff=False,
        is_superuser=False,
        is_active=True
    )


def reverse_initial_users(apps, schema_editor):
    """초기 사용자 삭제 (롤백용)"""
    User = apps.get_model('accounts', 'User')
    User.objects.filter(username__in=['admin', 'demo_user']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_users, reverse_initial_users),
    ]