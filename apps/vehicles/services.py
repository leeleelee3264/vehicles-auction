from typing import Dict, Any, Optional, List
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q, Prefetch
from django.contrib.auth import get_user_model

from apps.vehicles.models import Brand, CarType, Model, Vehicle, VehicleImage
from apps.vehicles.dto import VehicleCreateDTO
from apps.auctions.models import Auction

User = get_user_model()


class VehicleService:

    def create_vehicle(self, vehicle_data: VehicleCreateDTO) -> Vehicle:

        try:
            model = Model.objects.get(id=vehicle_data.model_id)
        except Model.DoesNotExist:
            raise ValidationError("유효하지 않은 모델입니다.")

        vehicle = Vehicle(
            model=model,
            year=vehicle_data.year,
            first_registration_date=vehicle_data.first_registration_date,
            color=vehicle_data.color,
            fuel_type=vehicle_data.fuel_type,
            transmission=vehicle_data.transmission,
            mileage=vehicle_data.mileage,
            region=vehicle_data.region
        )

        vehicle.full_clean()
        vehicle.save()

        # TODO:  여기서 말고 옥션 서비스를 호출해서 init하는 방식으로..? -> 서비스가 다른 서비스 호출
        Auction.objects.create(vehicle=vehicle)

        return vehicle

    @transaction.atomic
    def create_vehicle_with_images(self, vehicle_data: VehicleCreateDTO) -> Vehicle:

        self.validate_image_count(vehicle_data.images)

        vehicle = self.create_vehicle(vehicle_data)

        for index, image in enumerate(vehicle_data.images):
            VehicleImage.objects.create(
                vehicle=vehicle,
                image=image,
                is_primary=(index == 0)
            )

        return vehicle


    def validate_image_count(self, images: List) -> None:
        """이미지 개수 검증 (최소 5장)"""
        if len(images) < 5:
            raise ValidationError("차량 이미지는 최소 5장 이상 업로드해야 합니다.")


class FilterService:

    def get_filter_tree(self) -> Dict[str, Any]:

        # 모델별 차량 카운트
        models_with_count = Model.objects.annotate(
            vehicle_count=Count(
                'vehicle',
                filter=~Q(vehicle__auction__status=Auction.Status.PENDING)
            )
        ).select_related('car_type__brand')

        # 차종별 차량 카운트
        car_types_with_count = CarType.objects.annotate(
            vehicle_count=Count(
                'models__vehicle',
                filter=~Q(models__vehicle__auction__status=Auction.Status.PENDING)
            )
        ).select_related('brand').prefetch_related(
            Prefetch(
                'models',
                queryset=models_with_count
            )
        )

        # 브랜드별 차량 카운트
        brands = Brand.objects.annotate(
            vehicle_count=Count(
                'car_types__models__vehicle',
                filter=~Q(car_types__models__vehicle__auction__status=Auction.Status.PENDING)
            )
        ).prefetch_related(
            Prefetch(
                'car_types',
                queryset=car_types_with_count
            )
        )

        result = {'brands': []}

        for brand in brands:
            brand_data = {
                'id': brand.id,
                'name': brand.name,
                'count': brand.vehicle_count,
                'car_types': []
            }

            for car_type in brand.car_types.all():
                car_type_data = {
                    'id': car_type.id,
                    'name': car_type.name,
                    'count': car_type.vehicle_count,
                    'models': []
                }

                for model in car_type.models.all():
                    model_data = {
                        'id': model.id,
                        'name': model.name,
                        'count': model.vehicle_count
                    }
                    car_type_data['models'].append(model_data)

                brand_data['car_types'].append(car_type_data)

            result['brands'].append(brand_data)

        return result
