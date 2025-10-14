from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.core.exceptions import ValidationError, BadRequest

from apps.auctions.models import Auction
from apps.vehicles.models import Vehicle
from apps.vehicles.serializers import VehicleDetailSerializer
from apps.auctions.services import AuctionService


class VehicleApprovalView(APIView):
    permission_classes = [IsAdminUser]

    def __init__(self):
        super().__init__()
        self.auction_service = AuctionService()

    def post(self, request, pk):
        try:
            vehicle = self.auction_service.approve_auction(pk, request.user)

            response_serializer = VehicleDetailSerializer(
                vehicle,
                context={'request': request}
            )

            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )
        except Vehicle.DoesNotExist:
            return Response(
                {"detail": "존재하지 않는 차량입니다."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class VehicleTransactionCompleteView(APIView):
    permission_classes = [IsAdminUser]

    def __init__(self):
        super().__init__()
        self.auction_service = AuctionService()


    def post(self, request, pk):
        try:
            vehicle = self.auction_service.complete_transaction(pk, request.user)

            response_serializer = VehicleDetailSerializer(
                vehicle,
                context={'request': request}
            )

            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )

        except Vehicle.DoesNotExist:
            return Response(
                {"detail": "존재하지 않는 차량입니다."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
