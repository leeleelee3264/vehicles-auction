from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.accounts.dto import LoginDTO

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """로그인 요청 시리얼라이저"""

    username = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            'required': '사용자명을 입력해주세요.',
            'blank': '사용자명을 입력해주세요.'
        }
    )
    password = serializers.CharField(
        required=True,
        allow_blank=False,
        write_only=True,
        style={'input_type': 'password'},
        error_messages={
            'required': '비밀번호를 입력해주세요.',
            'blank': '비밀번호를 입력해주세요.'
        }
    )

    def to_dto(self) -> LoginDTO:
        return LoginDTO(**self.validated_data)



class UserSerializer(serializers.ModelSerializer):
    """사용자 정보 시리얼라이저"""

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_staff')
        read_only_fields = ('id', 'is_staff')
