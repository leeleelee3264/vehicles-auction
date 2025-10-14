from django.urls import path

from apps.auctions.views import VehicleApprovalView, VehicleTransactionCompleteView

urlpatterns = [

    path('<int:pk>/approve/', VehicleApprovalView.as_view(), name='vehicle-approve'),
    path('<int:pk>/complete/', VehicleTransactionCompleteView.as_view(), name='vehicle-complete')
]