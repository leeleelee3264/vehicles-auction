from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta, date
from unittest.mock import Mock, patch
import tempfile
from PIL import Image
import io

from apps.vehicles.models import Brand, CarType, Model, Vehicle, VehicleImage
from apps.vehicles.services import VehicleService, FilterService
from apps.vehicles.dto import VehicleCreateDTO
from apps.auctions.models import Auction

User = get_user_model()


class TestVehicleService(TestCase):
    """차량 서비스 레이어 테스트"""

    def setUp(self):

        self.user = User.objects.create_user(
            username='testuser_service',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='admintest_service',
            password='admin123',
            is_staff=True
        )

        # 브랜드, 차종, 모델 생성
        self.brand = Brand.objects.create(name="현대")
        self.car_type = CarType.objects.create(
            brand=self.brand,
            name="SUV"
        )
        self.model = Model.objects.create(
            car_type=self.car_type,
            name="싼타페"
        )

        # 서비스 인스턴스
        self.service = VehicleService()

    def test_create_vehicle_success(self):
        dto = VehicleCreateDTO(
            model_id=self.model.id,
            year=2023,
            first_registration_date=date(2023, 6, 15),
            color='흰색',
            fuel_type='gasoline',
            transmission='auto',
            mileage=15000,
            region='서울',
            images=[]
        )

        vehicle = self.service.create_vehicle(dto)

        self.assertIsNotNone(vehicle)
        self.assertEqual(vehicle.auction.status, Auction.Status.PENDING)
        self.assertEqual(vehicle.year, 2023)
        self.assertEqual(vehicle.model, self.model)

    def test_create_vehicle_auto_creates_auction(self):
        initial_auction_count = Auction.objects.count()

        dto = VehicleCreateDTO(
            model_id=self.model.id,
            year=2022,
            first_registration_date=date(2022, 3, 10),
            color='검정',
            fuel_type='diesel',
            transmission='manual',
            mileage=20000,
            region='부산',
            images=[]
        )

        vehicle = self.service.create_vehicle(dto)

        self.assertEqual(Auction.objects.count(), initial_auction_count + 1)
        self.assertTrue(hasattr(vehicle, 'auction'))
        self.assertIsNotNone(vehicle.auction)
        self.assertEqual(vehicle.auction.status, Auction.Status.PENDING)
        self.assertEqual(vehicle.auction.vehicle, vehicle)
        self.assertIsNone(vehicle.auction.start_time)
        self.assertIsNone(vehicle.auction.end_time)

    def test_create_vehicle_invalid_model(self):
        dto = VehicleCreateDTO(
            model_id=9999,  # 존재하지 않는 ID
            year=2023,
            first_registration_date=date(2023, 6, 15),
            color='검정',
            fuel_type='diesel',
            transmission='manual',
            mileage=5000,
            region='부산',
            images=[]
        )

        with self.assertRaises(ValidationError) as ctx:
            self.service.create_vehicle(dto)

        self.assertIn("모델", str(ctx.exception))

    @patch('apps.vehicles.models.VehicleImage.objects.create')
    def test_create_vehicle_with_images(self, mock_create_image):
        images = [Mock(name=f'test_{i}.jpg') for i in range(5)]

        dto = VehicleCreateDTO(
            model_id=self.model.id,
            year=2022,
            first_registration_date=date(2022, 3, 20),
            color='파란색',
            fuel_type='hybrid',
            transmission='auto',
            mileage=25000,
            region='경기',
            images=images
        )

        vehicle = self.service.create_vehicle_with_images(dto)

        self.assertIsNotNone(vehicle)

        self.assertEqual(mock_create_image.call_count, 5)
        first_call_args = mock_create_image.call_args_list[0]
        self.assertTrue(first_call_args[1]['is_primary'])


    def test_validate_image_count(self):
        # 5개 미만 이미지
        with self.assertRaises(ValidationError) as ctx:
            self.service.validate_image_count([1, 2, 3])

        self.assertIn("5장 이상", str(ctx.exception))

        # 5개 이상 이미지는 통과
        try:
            self.service.validate_image_count([1, 2, 3, 4, 5])
        except ValidationError:
            self.fail("5개 이상의 이미지는 검증을 통과해야 합니다")


class TestFilterService(TestCase):
    """필터 서비스 테스트"""

    def setUp(self):
        self.hyundai = Brand.objects.create(name="현대")
        self.kia = Brand.objects.create(name="기아")

        # 현대 차종
        self.hyundai_suv = CarType.objects.create(brand=self.hyundai, name="SUV")
        self.hyundai_sedan = CarType.objects.create(brand=self.hyundai, name="세단")

        # 기아 차종
        self.kia_suv = CarType.objects.create(brand=self.kia, name="SUV")

        # 모델
        self.palisade = Model.objects.create(car_type=self.hyundai_suv, name="팰리세이드")
        self.sonata = Model.objects.create(car_type=self.hyundai_sedan, name="소나타")
        self.sorento = Model.objects.create(car_type=self.kia_suv, name="쏘렌토")

        self.service = FilterService()

    def _create_vehicle(self, model, status=Auction.Status.AUCTION_ACTIVE):
        vehicle = Vehicle.objects.create(
            model=model,
            year=2023,
            first_registration_date=timezone.now().date() - timedelta(days=30),
            color='검정',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=5000,
            region='서울'
        )
        auction = Auction.objects.create(vehicle=vehicle, status=status)
        return vehicle

    def test_build_filter_tree_structure(self):
        self._create_vehicle(self.palisade, Auction.Status.AUCTION_ACTIVE)
        self._create_vehicle(self.sonata, Auction.Status.AUCTION_ENDED)
        self._create_vehicle(self.sorento, Auction.Status.TRANSACTION_COMPLETE)

        tree = self.service.get_filter_tree()

        # 예상 구조 검증
        self.assertIn('brands', tree)
        self.assertEqual(len(tree['brands']), 2)

    def test_filter_tree_excludes_pending(self):
        self._create_vehicle(self.palisade, Auction.Status.PENDING)
        self._create_vehicle(self.sonata, Auction.Status.PENDING)

        tree = self.service.get_filter_tree()

        # 현대 브랜드의 카운트가 0이어야 함
        hyundai_brand = next((b for b in tree['brands'] if b['id'] == self.hyundai.id), None)
        self.assertEqual(hyundai_brand['count'], 0)

    def test_filter_tree_counts_accuracy(self):
        # 현대 SUV 2대
        self._create_vehicle(self.palisade, Auction.Status.AUCTION_ACTIVE)
        self._create_vehicle(self.palisade, Auction.Status.AUCTION_ENDED)

        # 현대 세단 1대
        self._create_vehicle(self.sonata, Auction.Status.TRANSACTION_COMPLETE)

        # 기아 SUV 1대 + 승인대기 1대
        self._create_vehicle(self.sorento, Auction.Status.AUCTION_ACTIVE)
        self._create_vehicle(self.sorento, Auction.Status.PENDING)  # 제외


        tree = self.service.get_filter_tree()

        # 검증: 현대 3대, 기아 1대
        hyundai = next((b for b in tree['brands'] if b['id'] == self.hyundai.id), None)
        kia = next((b for b in tree['brands'] if b['id'] == self.kia.id), None)
        self.assertEqual(hyundai['count'], 3)
        self.assertEqual(kia['count'], 1)

    def test_filter_tree_with_no_vehicles(self):
        tree = self.service.get_filter_tree()

        for brand in tree['brands']:
            self.assertEqual(brand['count'], 0)
