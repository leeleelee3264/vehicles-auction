from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

from apps.vehicles.models import Brand, CarType, Model, Vehicle, VehicleImage
from apps.vehicles.services import FilterService
from apps.vehicles.dto import VehicleCreateDTO


class BrandSerializer(serializers.ModelSerializer):
    """브랜드 시리얼라이저"""
    class Meta:
        model = Brand
        fields = ['id', 'name']


class CarTypeSerializer(serializers.ModelSerializer):
    """차종 시리얼라이저"""
    class Meta:
        model = CarType
        fields = ['id', 'name']


class ModelSerializer(serializers.ModelSerializer):
    """모델 시리얼라이저"""
    class Meta:
        model = Model
        fields = ['id', 'name']


class VehicleImageSerializer(serializers.ModelSerializer):
    """차량 이미지 시리얼라이저"""
    class Meta:
        model = VehicleImage
        fields = ['id', 'image', 'is_primary']


class VehicleCreateSerializer(serializers.Serializer):

    model_id = serializers.IntegerField(required=True)
    year = serializers.IntegerField(required=True)
    first_registration_date = serializers.DateField(required=True)
    color = serializers.CharField(max_length=50, required=True)
    fuel_type = serializers.ChoiceField(
        choices=Vehicle.FuelType.choices,
        required=True
    )
    transmission = serializers.ChoiceField(
        choices=Vehicle.Transmission.choices,
        required=True
    )
    mileage = serializers.IntegerField(min_value=0, required=True)
    region = serializers.CharField(max_length=50, required=True)
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=True
    )

    def validate_model_id(self, value):

        try:
            Model.objects.get(id=value)
        except Model.DoesNotExist:
            raise serializers.ValidationError("유효하지 않은 모델입니다.")
        return value

    def validate_year(self, value):

        current_year = timezone.now().year
        if value > current_year:
            raise serializers.ValidationError("연식이 현재 년도보다 클 수 없습니다.")
        return value

    def validate_first_registration_date(self, value):

        if value > timezone.now().date():
            raise serializers.ValidationError("최초등록일이 미래일 수 없습니다.")
        return value

    def to_dto(self) -> VehicleCreateDTO:
        return VehicleCreateDTO(**self.validated_data)


class VehicleListSerializer(serializers.ModelSerializer):
    """차량 목록 시리얼라이저"""
    brand_name = serializers.CharField(source='model.car_type.brand.name', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)
    thumbnail_image = serializers.SerializerMethodField()
    status = serializers.CharField(source='auction.status', read_only=True)
    auction_end_time = serializers.DateTimeField(source='auction.end_time', read_only=True)
    remaining_seconds = serializers.IntegerField(source='auction.remaining_seconds', read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'id', 'brand_name', 'model_name', 'year',
            'mileage', 'fuel_type', 'status',
            'auction_end_time', 'remaining_seconds',
            'thumbnail_image', 'region'
        ]

    def get_thumbnail_image(self, obj):
        """대표 이미지 URL 반환"""
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            request = self.context.get('request')
            if request and primary_image.image:
                return request.build_absolute_uri(primary_image.image.url)
        return None


class VehicleDetailSerializer(serializers.ModelSerializer):
    """차량 상세 시리얼라이저"""
    brand = BrandSerializer(source='model.car_type.brand', read_only=True)
    car_type = CarTypeSerializer(source='model.car_type', read_only=True)
    model = ModelSerializer(read_only=True)
    images = VehicleImageSerializer(many=True, read_only=True)
    status = serializers.CharField(source='auction.status', read_only=True)
    auction_start_time = serializers.DateTimeField(source='auction.start_time', read_only=True)
    auction_end_time = serializers.DateTimeField(source='auction.end_time', read_only=True)
    remaining_seconds = serializers.IntegerField(source='auction.remaining_seconds', read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'id', 'brand', 'car_type', 'model',
            'year', 'first_registration_date',
            'color', 'fuel_type', 'transmission',
            'mileage', 'region', 'status',
            'auction_start_time', 'auction_end_time',
            'remaining_seconds', 'images'
        ]


class FilterModelSerializer(serializers.Serializer):
    """필터 트리 모델 시리얼라이저"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    count = serializers.IntegerField()


class FilterCarTypeSerializer(serializers.Serializer):
    """필터 트리 차종 시리얼라이저"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    count = serializers.IntegerField()
    models = FilterModelSerializer(many=True)


class FilterBrandSerializer(serializers.Serializer):
    """필터 트리 브랜드 시리얼라이저"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    count = serializers.IntegerField()
    car_types = FilterCarTypeSerializer(many=True)


class FilterTreeSerializer(serializers.Serializer):
    brands = FilterBrandSerializer(many=True)