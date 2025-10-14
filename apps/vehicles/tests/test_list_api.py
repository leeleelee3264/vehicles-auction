"""
Phase 7: 차량 목록 API 테스트
- 필터링 (브랜드/차종/모델)
- 정렬 (최근순/오래된순)
- 페이지네이션
- 남은 시간 계산
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta

from apps.vehicles.models import Brand, CarType, Model, Vehicle, VehicleImage
from apps.auctions.models import Auction

User = get_user_model()


class VehicleListAPITestCase(TestCase):
    """차량 목록 API 기본 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

        # 테스트 데이터 생성
        self.brand_hyundai = Brand.objects.create(name='현대')
        self.brand_kia = Brand.objects.create(name='기아')

        self.car_type_sonata = CarType.objects.create(brand=self.brand_hyundai, name='소나타')
        self.car_type_k5 = CarType.objects.create(brand=self.brand_kia, name='K5')

        self.model_sonata_dn8 = Model.objects.create(car_type=self.car_type_sonata, name='DN8')
        self.model_k5_dl3 = Model.objects.create(car_type=self.car_type_k5, name='DL3')

    def _create_vehicle(self, model, auction_status=Auction.Status.AUCTION_ACTIVE, **kwargs):
        defaults = {
            'year': 2020,
            'first_registration_date': timezone.now().date() - timedelta(days=365),
            'model': model,
            'color': '화이트',
            'fuel_type': Vehicle.FuelType.GASOLINE,
            'transmission': Vehicle.Transmission.AUTO,
            'mileage': 50000,
            'region': '서울'
        }

        defaults.update(kwargs)
        vehicle = Vehicle.objects.create(**defaults)

        auction_defaults = {'vehicle': vehicle, 'status': auction_status}
        if auction_status == Auction.Status.AUCTION_ACTIVE:
            auction_defaults['start_time'] = timezone.now() - timedelta(hours=24)
            auction_defaults['end_time'] = timezone.now() + timedelta(hours=24)

        Auction.objects.create(**auction_defaults)
        return vehicle

    def test_list_vehicles_excludes_pending(self):
        self._create_vehicle(self.model_sonata_dn8, auction_status=Auction.Status.PENDING)
        active_vehicle = self._create_vehicle(self.model_sonata_dn8, auction_status=Auction.Status.AUCTION_ACTIVE)
        ended_vehicle = self._create_vehicle(self.model_k5_dl3, auction_status=Auction.Status.AUCTION_ENDED)

        response = self.client.get('/api/vehicles/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        vehicle_ids = [v['id'] for v in response.data['results']]
        self.assertIn(active_vehicle.id, vehicle_ids)
        self.assertIn(ended_vehicle.id, vehicle_ids)

    def test_list_vehicles_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/vehicles/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class VehicleFilteringTestCase(TestCase):
    """차량 필터링 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

        # 브랜드/차종/모델 계층 구조 생성
        self.brand_hyundai = Brand.objects.create(name='현대')
        self.car_type_sedan = CarType.objects.create(brand=self.brand_hyundai, name='세단')
        self.car_type_suv = CarType.objects.create(brand=self.brand_hyundai, name='SUV')

        self.model_sonata = Model.objects.create(car_type=self.car_type_sedan, name='소나타')
        self.model_grandeur = Model.objects.create(car_type=self.car_type_sedan, name='그랜저')
        self.model_santafe = Model.objects.create(car_type=self.car_type_suv, name='싼타페')

        # 기아 브랜드
        self.brand_kia = Brand.objects.create(name='기아')
        self.car_type_kia_sedan = CarType.objects.create(brand=self.brand_kia, name='세단')
        self.model_k5 = Model.objects.create(car_type=self.car_type_kia_sedan, name='K5')

    def _create_public_vehicle(self, model, **kwargs):

        defaults = {
            'year': 2020,
            'first_registration_date': timezone.now().date() - timedelta(days=365),
            'model': model,
            'color': '화이트',
            'fuel_type': Vehicle.FuelType.GASOLINE,
            'transmission': Vehicle.Transmission.AUTO,
            'mileage': 50000,
            'region': '서울'
        }
        defaults.update(kwargs)
        vehicle = Vehicle.objects.create(**defaults)

        Auction.objects.create(
            vehicle=vehicle,
            status=Auction.Status.AUCTION_ACTIVE,
            start_time=timezone.now() - timedelta(hours=24),
            end_time=timezone.now() + timedelta(hours=24)
        )
        return vehicle

    def test_filter_by_brand(self):

        hyundai_1 = self._create_public_vehicle(self.model_sonata)
        hyundai_2 = self._create_public_vehicle(self.model_santafe)
        kia_1 = self._create_public_vehicle(self.model_k5)

        response = self.client.get('/api/vehicles/', {'brand': self.brand_hyundai.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        vehicle_ids = [v['id'] for v in response.data['results']]
        self.assertIn(hyundai_1.id, vehicle_ids)
        self.assertIn(hyundai_2.id, vehicle_ids)
        self.assertNotIn(kia_1.id, vehicle_ids)

    def test_filter_by_car_type(self):

        sedan_1 = self._create_public_vehicle(self.model_sonata)
        sedan_2 = self._create_public_vehicle(self.model_grandeur)
        suv_1 = self._create_public_vehicle(self.model_santafe)

        response = self.client.get('/api/vehicles/', {'car_type': self.car_type_sedan.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        vehicle_ids = [v['id'] for v in response.data['results']]
        self.assertIn(sedan_1.id, vehicle_ids)
        self.assertIn(sedan_2.id, vehicle_ids)
        self.assertNotIn(suv_1.id, vehicle_ids)

    def test_filter_by_model(self):

        sonata_1 = self._create_public_vehicle(self.model_sonata, year=2019)
        sonata_2 = self._create_public_vehicle(self.model_sonata, year=2020)
        grandeur = self._create_public_vehicle(self.model_grandeur)

        response = self.client.get('/api/vehicles/', {'model': self.model_sonata.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        vehicle_ids = [v['id'] for v in response.data['results']]
        self.assertIn(sonata_1.id, vehicle_ids)
        self.assertIn(sonata_2.id, vehicle_ids)
        self.assertNotIn(grandeur.id, vehicle_ids)

    def test_combined_filters(self):

        sonata = self._create_public_vehicle(self.model_sonata)
        grandeur = self._create_public_vehicle(self.model_grandeur)
        santafe = self._create_public_vehicle(self.model_santafe)
        k5 = self._create_public_vehicle(self.model_k5)

        response = self.client.get('/api/vehicles/', {
            'brand': self.brand_hyundai.id,
            'car_type': self.car_type_sedan.id
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        vehicle_ids = [v['id'] for v in response.data['results']]
        self.assertIn(sonata.id, vehicle_ids)
        self.assertIn(grandeur.id, vehicle_ids)
        self.assertNotIn(santafe.id, vehicle_ids)
        self.assertNotIn(k5.id, vehicle_ids)


class VehicleSortingTestCase(TestCase):
    """차량 정렬 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

        # 테스트 모델 생성
        self.brand = Brand.objects.create(name='현대')
        self.car_type = CarType.objects.create(brand=self.brand, name='세단')
        self.model = Model.objects.create(car_type=self.car_type, name='소나타')

    def test_sort_by_auction_start_time_desc(self):

        now = timezone.now()
        vehicle_1 = Vehicle.objects.create(
            year=2020,
            first_registration_date=timezone.now().date(),
            model=self.model,
            color='화이트',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=10000,
            region='서울'
        )
        Auction.objects.create(
            vehicle=vehicle_1,
            status=Auction.Status.AUCTION_ACTIVE,
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=47)
        )

        vehicle_2 = Vehicle.objects.create(
            year=2021,
            first_registration_date=timezone.now().date(),
            model=self.model,
            color='블랙',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=20000,
            region='부산'
        )
        Auction.objects.create(
            vehicle=vehicle_2,
            status=Auction.Status.AUCTION_ACTIVE,
            start_time=now - timedelta(hours=10),
            end_time=now + timedelta(hours=38)
        )

        vehicle_3 = Vehicle.objects.create(
            year=2019,
            first_registration_date=timezone.now().date(),
            model=self.model,
            color='그레이',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=30000,
            region='대구'
        )
        Auction.objects.create(
            vehicle=vehicle_3,
            status=Auction.Status.AUCTION_ACTIVE,
            start_time=now - timedelta(hours=5),
            end_time=now + timedelta(hours=43)
        )

        response = self.client.get('/api/vehicles/', {'sort': '-auction__start_time'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

        results = response.data['results']
        self.assertEqual(results[0]['id'], vehicle_1.id)  # 1시간 전
        self.assertEqual(results[1]['id'], vehicle_3.id)  # 5시간 전
        self.assertEqual(results[2]['id'], vehicle_2.id)  # 10시간 전

    def test_sort_by_auction_start_time_asc(self):
        now = timezone.now()
        vehicle_1 = Vehicle.objects.create(
            year=2020,
            first_registration_date=timezone.now().date(),
            model=self.model,
            color='화이트',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=10000,
            region='서울'
        )
        Auction.objects.create(
            vehicle=vehicle_1,
            status=Auction.Status.AUCTION_ACTIVE,
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=47)
        )

        vehicle_2 = Vehicle.objects.create(
            year=2021,
            first_registration_date=timezone.now().date(),
            model=self.model,
            color='블랙',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=20000,
            region='부산'
        )
        Auction.objects.create(
            vehicle=vehicle_2,
            status=Auction.Status.AUCTION_ACTIVE,
            start_time=now - timedelta(hours=10),
            end_time=now + timedelta(hours=38)
        )

        response = self.client.get('/api/vehicles/', {'sort': 'auction__start_time'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(results[0]['id'], vehicle_2.id)  # 10시간 전
        self.assertEqual(results[1]['id'], vehicle_1.id)  # 1시간 전

    def test_default_sort_without_param(self):
        now = timezone.now()
        vehicle_old = Vehicle.objects.create(
            year=2020,
            first_registration_date=timezone.now().date(),
            model=self.model,
            color='화이트',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=10000,
            region='서울'
        )
        Auction.objects.create(
            vehicle=vehicle_old,
            status=Auction.Status.AUCTION_ACTIVE,
            start_time=now - timedelta(hours=10),
            end_time=now + timedelta(hours=38)
        )

        vehicle_new = Vehicle.objects.create(
            year=2021,
            first_registration_date=timezone.now().date(),
            model=self.model,
            color='블랙',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=20000,
            region='부산'
        )
        Auction.objects.create(
            vehicle=vehicle_new,
            status=Auction.Status.AUCTION_ACTIVE,
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=47)
        )

        response = self.client.get('/api/vehicles/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(results[0]['id'], vehicle_new.id)  # 1시간 전 (최신)
        self.assertEqual(results[1]['id'], vehicle_old.id)  # 10시간 전 (오래된)


class VehiclePaginationTestCase(TestCase):
    """차량 페이지네이션 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

        # 테스트 모델 생성
        self.brand = Brand.objects.create(name='현대')
        self.car_type = CarType.objects.create(brand=self.brand, name='세단')
        self.model = Model.objects.create(car_type=self.car_type, name='소나타')

        for i in range(25):
            vehicle = Vehicle.objects.create(
                year=2020 + (i % 3),
                first_registration_date=timezone.now().date(),
                model=self.model,
                color='화이트',
                fuel_type=Vehicle.FuelType.GASOLINE,
                transmission=Vehicle.Transmission.AUTO,
                mileage=10000 + (i * 1000),
                region='서울'
            )
            Auction.objects.create(
                vehicle=vehicle,
                status=Auction.Status.AUCTION_ACTIVE,
                start_time=timezone.now() - timedelta(hours=i),
                end_time=timezone.now() + timedelta(hours=48-i)
            )

    def test_pagination_default_page_size(self):
        response = self.client.get('/api/vehicles/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 25)
        self.assertEqual(len(response.data['results']), 20)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

    def test_pagination_second_page(self):
        response = self.client.get('/api/vehicles/', {'page': 2})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 25)
        self.assertEqual(len(response.data['results']), 5)
        self.assertIsNone(response.data['next'])
        self.assertIsNotNone(response.data['previous'])

    def test_pagination_with_page_size(self):
        response = self.client.get('/api/vehicles/', {'page_size': 10})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIsNotNone(response.data['next'])


class VehicleRemainingTimeTestCase(TestCase):
    """남은 시간 계산 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

        # 테스트 모델 생성
        self.brand = Brand.objects.create(name='현대')
        self.car_type = CarType.objects.create(brand=self.brand, name='세단')
        self.model = Model.objects.create(car_type=self.car_type, name='소나타')

    def test_remaining_seconds_for_active_auction(self):
        now = timezone.now()
        vehicle = Vehicle.objects.create(
            year=2020,
            first_registration_date=timezone.now().date(),
            model=self.model,
            color='화이트',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=10000,
            region='서울'
        )
        Auction.objects.create(
            vehicle=vehicle,
            status=Auction.Status.AUCTION_ACTIVE,
            start_time=now - timedelta(hours=24),
            end_time=now + timedelta(hours=24)
        )

        response = self.client.get('/api/vehicles/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        vehicle_data = response.data['results'][0]
        self.assertIn('remaining_seconds', vehicle_data)

        # 약 24시간(86400초) 남음 (오차 60초 허용)
        self.assertGreater(vehicle_data['remaining_seconds'], 86340)
        self.assertLess(vehicle_data['remaining_seconds'], 86460)

    def test_remaining_seconds_for_ended_auction(self):
        vehicle = Vehicle.objects.create(
            year=2020,
            first_registration_date=timezone.now().date(),
            model=self.model,
            color='화이트',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=10000,
            region='서울'
        )
        Auction.objects.create(
            vehicle=vehicle,
            status=Auction.Status.AUCTION_ENDED,
            start_time=timezone.now() - timedelta(hours=50),
            end_time=timezone.now() - timedelta(hours=2)
        )

        response = self.client.get('/api/vehicles/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vehicle_data = response.data['results'][0]
        self.assertEqual(vehicle_data['remaining_seconds'], 0)

    def test_remaining_seconds_for_transaction_complete(self):
        vehicle = Vehicle.objects.create(
            year=2020,
            first_registration_date=timezone.now().date(),
            model=self.model,
            color='화이트',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=10000,
            region='서울'
        )
        Auction.objects.create(
            vehicle=vehicle,
            status=Auction.Status.TRANSACTION_COMPLETE,
            completed_at=timezone.now()
        )

        response = self.client.get('/api/vehicles/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vehicle_data = response.data['results'][0]
        self.assertEqual(vehicle_data['remaining_seconds'], 0)
