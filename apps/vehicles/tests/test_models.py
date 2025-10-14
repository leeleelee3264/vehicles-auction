from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta

from apps.vehicles.models import Brand, CarType, Model, Vehicle, VehicleImage


class TestVehicleModel(TestCase):
    """차량 모델 테스트"""

    def setUp(self):
        # 브랜드, 차종, 모델 생성
        self.brand = Brand.objects.create(name="현대")
        self.car_type = CarType.objects.create(
            brand=self.brand,
            name="SUV"
        )
        self.model = Model.objects.create(
            car_type=self.car_type,
            name="팰리세이드"
        )

        # 기본 차량 데이터
        self.valid_vehicle_data = {
            'model': self.model,
            'year': 2023,
            'first_registration_date': timezone.now().date() - timedelta(days=30),
            'color': '검정',
            'fuel_type': Vehicle.FuelType.GASOLINE,
            'transmission': Vehicle.Transmission.AUTO,
            'mileage': 5000,
            'region': '서울'
        }

    def test_create_vehicle_success(self):
        vehicle = Vehicle.objects.create(**self.valid_vehicle_data)

        self.assertIsNotNone(vehicle.id)
        self.assertEqual(vehicle.year, 2023)
        self.assertEqual(vehicle.model.name, "팰리세이드")

    def test_vehicle_string_representation(self):
        vehicle = Vehicle.objects.create(**self.valid_vehicle_data)

        expected_str = f"{self.model} (2023년식)"
        self.assertEqual(str(vehicle), expected_str)

    def test_vehicle_model_relationship(self):
        vehicle = Vehicle.objects.create(**self.valid_vehicle_data)

        self.assertEqual(vehicle.model, self.model)
        self.assertEqual(vehicle.model.name, "팰리세이드")
        self.assertEqual(vehicle.model.car_type, self.car_type)
        self.assertEqual(vehicle.model.car_type.brand, self.brand)

    def test_delete_vehicle_cascades_images(self):
        vehicle = Vehicle.objects.create(**self.valid_vehicle_data)

        image1 = VehicleImage.objects.create(
            vehicle=vehicle,
            image='test1.jpg',
            is_primary=True
        )
        image2 = VehicleImage.objects.create(
            vehicle=vehicle,
            image='test2.jpg',
            is_primary=False
        )

        self.assertEqual(VehicleImage.objects.filter(vehicle=vehicle).count(), 2)

        vehicle_id = vehicle.id
        vehicle.delete()

        self.assertEqual(VehicleImage.objects.filter(vehicle_id=vehicle_id).count(), 0)



class TestVehicleImageModel(TestCase):
    """차량 이미지 모델 테스트"""

    def setUp(self):
        """테스트용 데이터 준비"""
        brand = Brand.objects.create(name="기아")
        car_type = CarType.objects.create(brand=brand, name="세단")
        model = Model.objects.create(car_type=car_type, name="K5")

        self.vehicle = Vehicle.objects.create(
            model=model,
            year=2022,
            first_registration_date=timezone.now().date() - timedelta(days=365),
            color='흰색',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=10000,
            region='부산'
        )

    def test_create_vehicle_image(self):
        image = VehicleImage.objects.create(
            vehicle=self.vehicle,
            image='test.jpg',
            is_primary=True
        )

        self.assertIsNotNone(image.id)
        self.assertEqual(image.vehicle, self.vehicle)
        self.assertTrue(image.is_primary)

    def test_multiple_images_for_vehicle(self):
        for i in range(5):
            VehicleImage.objects.create(
                vehicle=self.vehicle,
                image=f'test_{i}.jpg',
                is_primary=(i == 0)
            )

        images = VehicleImage.objects.filter(vehicle=self.vehicle)
        self.assertEqual(images.count(), 5)
        self.assertEqual(images.filter(is_primary=True).count(), 1)


class TestBrandCarTypeModel(TestCase):
    """브랜드, 차종, 모델 계층구조 테스트"""

    def test_brand_car_type_relationship(self):
        brand = Brand.objects.create(name="현대")

        suv = CarType.objects.create(brand=brand, name="SUV")
        sedan = CarType.objects.create(brand=brand, name="세단")

        self.assertEqual(brand.car_types.count(), 2)
        self.assertEqual(suv.brand, brand)
        self.assertEqual(sedan.brand, brand)

    def test_car_type_model_relationship(self):
        brand = Brand.objects.create(name="기아")
        suv = CarType.objects.create(brand=brand, name="SUV")

        sorento = Model.objects.create(car_type=suv, name="쏘렌토")
        carnival = Model.objects.create(car_type=suv, name="카니발")

        self.assertEqual(suv.models.count(), 2)
        self.assertEqual(sorento.car_type, suv)
        self.assertEqual(carnival.car_type, suv)

    def test_brand_unique_constraint(self):
        Brand.objects.create(name="현대")

        with self.assertRaises(Exception):  # IntegrityError
            Brand.objects.create(name="현대")

    def test_car_type_unique_together(self):
        brand = Brand.objects.create(name="현대")
        CarType.objects.create(brand=brand, name="SUV")

        with self.assertRaises(Exception):  # IntegrityError
            CarType.objects.create(brand=brand, name="SUV")

    def test_model_unique_together(self):
        brand = Brand.objects.create(name="현대")
        suv = CarType.objects.create(brand=brand, name="SUV")
        Model.objects.create(car_type=suv, name="팰리세이드")

        with self.assertRaises(Exception):  # IntegrityError
            Model.objects.create(car_type=suv, name="팰리세이드")
