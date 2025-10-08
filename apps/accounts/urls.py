from django.urls import path
from apps.accounts.views import LoginView

app_name = 'accounts'

urlpatterns = [
    # JWT 로그인 엔드포인트 (클래스 기반 뷰)
    path('login/', LoginView.as_view(), name='login'),
]