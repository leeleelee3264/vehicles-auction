"""
URL configuration for vehicle auction project.
"""
from django.urls import path, include

urlpatterns = [
    # Admin 사용하지 않음 (JWT API 전용)
    # path('admin/', admin.site.urls),

    # API URLs will be added in Phase 2
    # path('api/auth/', include('apps.accounts.urls')),
    # path('api/vehicles/', include('apps.vehicles.urls')),
]