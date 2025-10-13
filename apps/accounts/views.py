from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.serializers import LoginSerializer, UserSerializer
from apps.accounts.services import JWTService, AccountService


class LoginView(APIView):

    permission_classes = [AllowAny]

    def __init__(self):

        super().__init__()
        self.jwt_service = JWTService()
        self.account_service = AccountService()

    def post(self, request):

        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )


        user = self.account_service.authenticate_user(serializer.to_dto())

        if not user:
            return Response(
                {'error': '아이디 또는 비밀번호가 올바르지 않습니다.'},
                status=status.HTTP_401_UNAUTHORIZED
            )


        tokens = self.jwt_service.create_tokens_for_user(user)

        user_serializer = UserSerializer(user)

        return Response({
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'user': user_serializer.data
        }, status=status.HTTP_200_OK)