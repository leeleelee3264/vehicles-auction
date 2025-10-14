from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from PIL import Image
import io
import json

from apps.vehicles.models import Brand, CarType, Model, Vehicle, VehicleImage
from apps.auctions.models import Auction

User = get_user_model()


class TestVehicleCreateAPI(TestCase):
    """차량 등록 API 테스트"""

    def setUp(self):
        self.client = APIClient()

        # 테스트 사용자
        self.user = User.objects.create_user(
            username='testuser_create',
            password='testpass123'
        )

        # JWT 토큰 발급 (실제로는 login API 호출)
        self.client.force_authenticate(user=self.user)

        # 브랜드, 차종, 모델 생성
        self.brand = Brand.objects.create(name="현대")
        self.car_type = CarType.objects.create(
            brand=self.brand,
            name="SUV"
        )
        self.model = Model.objects.create(
            car_type=self.car_type,
            name="투싼"
        )

    def _create_test_image(self, name='test.jpg'):
        img = Image.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(name, img_io.read(), content_type='image/jpeg')

    def test_create_vehicle_with_images_success(self):
        images = [self._create_test_image(f'test_{i}.jpg') for i in range(5)]

        data = {
            'model_id': self.model.id,
            'year': 2023,
            'first_registration_date': '2023-06-15',
            'color': '검정',
            'fuel_type': 'gasoline',
            'transmission': 'auto',
            'mileage': 5000,
            'region': '서울',
            'images': images
        }

        response = self.client.post(
            reverse('vehicle-create'),
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['status'], 'PENDING')

        vehicle = Vehicle.objects.get(id=response.data['id'])
        self.assertEqual(vehicle.images.count(), 5)

    def test_create_vehicle_insufficient_images(self):
        images = [self._create_test_image(f'test_{i}.jpg') for i in range(3)]

        data = {
            'model_id': self.model.id,
            'year': 2023,
            'first_registration_date': '2023-06-15',
            'color': '흰색',
            'fuel_type': 'diesel',
            'transmission': 'manual',
            'mileage': 10000,
            'region': '부산',
            'images': images
        }

        response = self.client.post(
            reverse('vehicle-create'),
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # self.assertIn('images', response.data)
        self.assertIn('5장 이상', str(response.data['error']))

    def test_create_vehicle_missing_required_fields(self):
        images = [self._create_test_image(f'test_{i}.jpg') for i in range(5)]

        data = {
            # model_id 누락
            'year': 2023,
            'first_registration_date': '2023-06-15',
            'color': '파랑',
            'fuel_type': 'hybrid',
            'transmission': 'auto',
            'mileage': 15000,
            'region': '대구',
            'images': images
        }

        response = self.client.post(
            reverse('vehicle-create'),
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('model_id', response.data)

    def test_create_vehicle_invalid_model_id(self):
        images = [self._create_test_image(f'test_{i}.jpg') for i in range(5)]

        data = {
            'model_id': 9999,  # 존재하지 않는 모델 ID
            'year': 2023,
            'first_registration_date': '2023-06-15',
            'color': '회색',
            'fuel_type': 'electric',
            'transmission': 'auto',
            'mileage': 0,
            'region': '인천',
            'images': images
        }

        response = self.client.post(
            reverse('vehicle-create'),
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('model_id', response.data)

    def test_create_vehicle_without_authentication(self):
        self.client.force_authenticate(user=None)
        images = [self._create_test_image(f'test_{i}.jpg') for i in range(5)]

        data = {
            'model_id': self.model.id,
            'year': 2023,
            'first_registration_date': '2023-06-15',
            'color': '녹색',
            'fuel_type': 'lpg',
            'transmission': 'manual',
            'mileage': 20000,
            'region': '광주',
            'images': images
        }

        response = self.client.post(
            reverse('vehicle-create'),
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_vehicle_invalid_year(self):
        images = [self._create_test_image(f'test_{i}.jpg') for i in range(5)]

        data = {
            'model_id': self.model.id,
            'year': timezone.now().year + 1,  # 미래 연도
            'first_registration_date': '2023-06-15',
            'color': '빨강',
            'fuel_type': 'bifuel',
            'transmission': 'auto',
            'mileage': 25000,
            'region': '전주',
            'images': images
        }

        response = self.client.post(
            reverse('vehicle-create'),
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('year', response.data)

    def test_create_vehicle_future_registration_date(self):
        images = [self._create_test_image(f'test_{i}.jpg') for i in range(5)]

        future_date = (timezone.now().date() + timedelta(days=30)).isoformat()

        data = {
            'model_id': self.model.id,
            'year': 2023,
            'first_registration_date': future_date,  # 미래 날짜
            'color': '노랑',
            'fuel_type': 'bifuel',
            'transmission': 'auto',
            'mileage': 25000,
            'region': '전주',
            'images': images
        }

        response = self.client.post(
            reverse('vehicle-create'),
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_registration_date', response.data)


class TestVehicleDetailAPI(TestCase):
    """차량 상세 조회 API 테스트"""

    def setUp(self):
        self.client = APIClient()

        # 테스트 사용자
        self.user = User.objects.create_user(
            username='testuser_detail',
            password='testpass123'
        )

        # JWT 토큰 발급
        self.client.force_authenticate(user=self.user)

        brand = Brand.objects.create(name="기아")
        car_type = CarType.objects.create(brand=brand, name="세단")
        model = Model.objects.create(car_type=car_type, name="K8")

        self.public_vehicle = Vehicle.objects.create(
            model=model,
            year=2022,
            first_registration_date='2022-03-20',
            color='검정',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=15000,
            region='서울'
        )
        public_auction = Auction.objects.create(
            vehicle=self.public_vehicle,
            status=Auction.Status.AUCTION_ACTIVE,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=24)
        )

        self.private_vehicle = Vehicle.objects.create(
            model=model,
            year=2021,
            first_registration_date='2021-05-10',
            color='흰색',
            fuel_type=Vehicle.FuelType.HYBRID,
            transmission=Vehicle.Transmission.AUTO,
            mileage=25000,
            region='부산'
        )
        private_auction = Auction.objects.create(
            vehicle=self.private_vehicle,
            status=Auction.Status.PENDING
        )

        for i in range(3):
            VehicleImage.objects.create(
                vehicle=self.public_vehicle,
                image=f'test_{i}.jpg',
                is_primary=(i == 0)
            )

    def test_get_vehicle_detail_success(self):
        response = self.client.get(
            reverse('vehicle-detail', kwargs={'pk': self.public_vehicle.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.public_vehicle.id)
        self.assertEqual(response.data['year'], 2022)
        self.assertEqual(response.data['status'], 'AUCTION_ACTIVE')

        # 브랜드, 차종, 모델 정보 확인
        self.assertEqual(response.data['brand']['name'], '기아')
        self.assertEqual(response.data['car_type']['name'], '세단')
        self.assertEqual(response.data['model']['name'], 'K8')

        # 이미지 정보 확인
        self.assertEqual(len(response.data['images']), 3)
        self.assertTrue(response.data['images'][0]['is_primary'])

    def test_get_vehicle_detail_with_remaining_time(self):
        response = self.client.get(
            reverse('vehicle-detail', kwargs={'pk': self.public_vehicle.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('remaining_seconds', response.data)
        self.assertGreater(response.data['remaining_seconds'], 0)

    def test_get_vehicle_detail_private_vehicle(self):
        response = self.client.get(
            reverse('vehicle-detail', kwargs={'pk': self.private_vehicle.id})
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_vehicle_detail_not_found(self):
        response = self.client.get(
            reverse('vehicle-detail', kwargs={'pk': 9999})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_vehicle_detail_without_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(
            reverse('vehicle-detail', kwargs={'pk': self.public_vehicle.id})
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_vehicle_detail_includes_all_fields(self):
        response = self.client.get(
            reverse('vehicle-detail', kwargs={'pk': self.public_vehicle.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 필수 필드들 확인
        required_fields = [
            'id', 'brand', 'car_type', 'model',
            'year', 'first_registration_date',
            'color', 'fuel_type', 'transmission',
            'mileage', 'region', 'status',
            'auction_start_time', 'auction_end_time',
            'images'
        ]

        for field in required_fields:
            self.assertIn(field, response.data)


class TestVehicleFilterAPI(TestCase):
    """차량 필터 API 테스트"""

    def setUp(self):
        self.client = APIClient()

        # 테스트 사용자
        self.user = User.objects.create_user(
            username='testuser_filter',
            password='testpass123'
        )

        # 인증
        self.client.force_authenticate(user=self.user)

        self._create_test_data()

    def _create_test_data(self):
        # 브랜드
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

        self._create_vehicles()

    def _create_vehicles(self):
        base_date = timezone.now().date() - timedelta(days=30)

        # 현대 SUV - 팰리세이드 2대 (공개)
        for i in range(2):
            vehicle = Vehicle.objects.create(
                model=self.palisade,
                year=2023,
                first_registration_date=base_date,
                color='검정',
                fuel_type=Vehicle.FuelType.GASOLINE,
                transmission=Vehicle.Transmission.AUTO,
                mileage=5000 + i * 1000,
                region='서울'
            )
            auction_status = Auction.Status.AUCTION_ACTIVE if i == 0 else Auction.Status.AUCTION_ENDED
            Auction.objects.create(vehicle=vehicle, status=auction_status)

        # 현대 세단 - 소나타 1대 (공개) + 1대 (승인대기)
        vehicle1 = Vehicle.objects.create(
            model=self.sonata,
            year=2023,
            first_registration_date=base_date,
            color='흰색',
            fuel_type=Vehicle.FuelType.HYBRID,
            transmission=Vehicle.Transmission.AUTO,
            mileage=10000,
            region='부산'
        )
        Auction.objects.create(vehicle=vehicle1, status=Auction.Status.TRANSACTION_COMPLETE)

        vehicle2 = Vehicle.objects.create(
            model=self.sonata,
            year=2022,
            first_registration_date=base_date,
            color='회색',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=20000,
            region='대구'
        )
        Auction.objects.create(vehicle=vehicle2, status=Auction.Status.PENDING)

        # 기아 SUV - 쏘렌토 1대 (공개)
        vehicle3 = Vehicle.objects.create(
            model=self.sorento,
            year=2023,
            first_registration_date=base_date,
            color='파랑',
            fuel_type=Vehicle.FuelType.DIESEL,
            transmission=Vehicle.Transmission.AUTO,
            mileage=8000,
            region='인천'
        )
        Auction.objects.create(vehicle=vehicle3, status=Auction.Status.AUCTION_ACTIVE)

    def test_get_filter_tree_success(self):
        response = self.client.get(reverse('vehicle-filters'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('brands', response.data)

    def test_filter_tree_response_structure(self):
        response = self.client.get(reverse('vehicle-filters'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 브랜드 레벨 검증
        brands = response.data['brands']
        self.assertIsInstance(brands, list)
        self.assertEqual(len(brands), 2)

        # 현대 브랜드 검증
        hyundai = next((b for b in brands if b['name'] == '현대'), None)
        self.assertIsNotNone(hyundai)
        self.assertEqual(hyundai['count'], 3)

        # 차종 레벨 검증
        self.assertIn('car_types', hyundai)
        car_types = hyundai['car_types']
        self.assertEqual(len(car_types), 2)  # SUV, 세단

        # 모델 레벨 검증
        suv = next((ct for ct in car_types if ct['name'] == 'SUV'), None)
        self.assertIsNotNone(suv)
        self.assertIn('models', suv)

    def test_filter_tree_requires_authentication(self):
        self.client.force_authenticate(user=None)  # 인증 해제

        response = self.client.get(reverse('vehicle-filters'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filter_counts_match_actual_vehicles(self):
        response = self.client.get(reverse('vehicle-filters'))

        # 현대 브랜드 카운트 확인 (3대: 팰리세이드 2 + 소나타 1)
        hyundai = next((b for b in response.data['brands'] if b['id'] == self.hyundai.id), None)
        self.assertEqual(hyundai['count'], 3)

        # 현대 SUV 카운트 확인 (2대: 팰리세이드)
        hyundai_suv = next((ct for ct in hyundai['car_types'] if ct['id'] == self.hyundai_suv.id), None)
        self.assertEqual(hyundai_suv['count'], 2)

        # 현대 세단 카운트 확인 (1대: 소나타, 승인대기 제외)
        hyundai_sedan = next((ct for ct in hyundai['car_types'] if ct['id'] == self.hyundai_sedan.id), None)
        self.assertEqual(hyundai_sedan['count'], 1)

        # 기아 브랜드 카운트 확인 (1대: 쏘렌토)
        kia = next((b for b in response.data['brands'] if b['id'] == self.kia.id), None)
        self.assertEqual(kia['count'], 1)

    def test_filter_tree_realtime_update(self):
        # 첫 번째 요청
        response1 = self.client.get(reverse('vehicle-filters'))
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # 현대 브랜드의 초기 카운트 확인
        hyundai1 = next((b for b in response1.data['brands'] if b['name'] == '현대'), None)
        initial_count = hyundai1['count']

        # 새 차량 추가
        new_vehicle = Vehicle.objects.create(
            model=self.palisade,
            year=2023,
            first_registration_date=timezone.now().date(),
            color='빨강',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=1000,
            region='광주'
        )
        Auction.objects.create(vehicle=new_vehicle, status=Auction.Status.AUCTION_ACTIVE)

        # 두 번째 요청 (실시간으로 업데이트된 카운트 확인)
        response2 = self.client.get(reverse('vehicle-filters'))

        # 현대 브랜드 카운트가 즉시 증가했는지 확인
        hyundai2 = next((b for b in response2.data['brands'] if b['name'] == '현대'), None)
        self.assertEqual(hyundai2['count'], initial_count + 1)

    def test_empty_filter_tree(self):
        # 모든 차량 삭제 (Auction도 함께 삭제)
        Auction.objects.all().delete()
        Vehicle.objects.all().delete()

        response = self.client.get(reverse('vehicle-filters'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        brands = response.data['brands']

        for brand in brands:
            self.assertEqual(brand['count'], 0)
