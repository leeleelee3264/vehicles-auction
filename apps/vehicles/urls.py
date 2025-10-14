from django.urls import path
from apps.vehicles.views import (
    VehicleListView,
    VehicleCreateView,
    VehicleDetailView,
    VehicleFilterView
)

urlpatterns = [
    path('', VehicleListView.as_view(), name='vehicle-list'),
    path('create/', VehicleCreateView.as_view(), name='vehicle-create'),
    path('filters/', VehicleFilterView.as_view(), name='vehicle-filters'),
    path('<int:pk>/', VehicleDetailView.as_view(), name='vehicle-detail')
]