from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser

from apps.vehicles.models import Vehicle
from apps.vehicles.serializers import (
    VehicleCreateSerializer,
    VehicleDetailSerializer,
    VehicleListSerializer,
    FilterTreeSerializer
)
from apps.vehicles.services import VehicleService, FilterService
from apps.vehicles.pagination import VehicleListPagination
from apps.auctions.models import Auction

class VehicleListView(ListAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = VehicleListSerializer
    pagination_class = VehicleListPagination

    def get_queryset(self):

        queryset = Vehicle.objects.exclude(
            auction__status=Auction.Status.PENDING
        ).select_related(
            'model__car_type__brand',
            'auction'
        ).prefetch_related(
            'images'
        )

        # 필터 파라미터 처리
        brand_id = self.request.query_params.get('brand', None)
        car_type_id = self.request.query_params.get('car_type', None)
        model_id = self.request.query_params.get('model', None)

        if brand_id:
            queryset = queryset.filter(model__car_type__brand_id=brand_id)
        if car_type_id:
            queryset = queryset.filter(model__car_type_id=car_type_id)
        if model_id:
            queryset = queryset.filter(model_id=model_id)

        # 정렬 파라미터 처리 (기본값: 경매시작 최신순)
        ALLOWED_SORTS = ['-auction__start_time', 'auction__start_time']
        sort_param = self.request.query_params.get('sort', '-auction__start_time')
        if sort_param in ALLOWED_SORTS:
            queryset = queryset.order_by(sort_param)

        return queryset


class VehicleCreateView(APIView):

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def __init__(self):
        super().__init__()
        self.vehicle_service = VehicleService()

    def post(self, request):
        serializer = VehicleCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            vehicle = self.vehicle_service.create_vehicle_with_images(serializer.to_dto())
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        response_serializer = VehicleDetailSerializer(
            vehicle,
            context={'request': request}
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )


class VehicleDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VehicleDetailSerializer

    def get_queryset(self):
        return Vehicle.objects.select_related(
            'model__car_type__brand',
            'auction'
        ).prefetch_related(
            'images'
        )

    def get_object(self):
        from apps.auctions.models import Auction

        pk = self.kwargs.get('pk')

        try:
            vehicle = self.get_queryset().get(pk=pk)
        except Vehicle.DoesNotExist:
            raise NotFound(detail="존재하지 않는 차량입니다.")

        if vehicle.auction.status == Auction.Status.PENDING:
            raise PermissionDenied(
                detail="승인 대기 중인 차량은 조회할 수 없습니다."
            )

        return vehicle


class VehicleFilterView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self):
        super().__init__()
        self.filter_service = FilterService()


    def get(self, request):

        filter_tree = self.filter_service.get_filter_tree()

        serializer = FilterTreeSerializer(filter_tree)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )