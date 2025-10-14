"""
URL configuration for vehicle auction project.
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('api/auth/', include('apps.accounts.urls')),
    path('api/vehicles/', include('apps.vehicles.urls')),
    path('api/auctions/', include('apps.auctions.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)