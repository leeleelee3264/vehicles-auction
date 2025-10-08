"""
URL configuration for vehicle auction project.
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin 사용하지 않음 (JWT API 전용)
    # path('admin/', admin.site.urls),

    # API URLs
    path('api/auth/', include('apps.accounts.urls')),
    # path('api/vehicles/', include('apps.vehicles.urls')),  # Phase 3에서 구현
    # path('api/auctions/', include('apps.auctions.urls')),  # Phase 3에서 구현
]

# 개발 환경에서 미디어 파일 제공
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)