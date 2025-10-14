from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from unittest.mock import patch, MagicMock

from apps.vehicles.models import Brand, CarType, Model, Vehicle
from apps.auctions.models import Auction, AuctionHistory
from apps.auctions.services import AuctionService

User = get_user_model()


class AuctionApprovalTestCase(TestCase):
    """경매 승인 API 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='test_admin',
            password='adminpass',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='test_user',
            password='userpass'
        )

        self.brand = Brand.objects.create(name='현대')
        self.car_type = CarType.objects.create(brand=self.brand, name='SUV')
        self.model = Model.objects.create(car_type=self.car_type, name='팰리세이드')

    def _create_vehicle(self, auction_status=Auction.Status.PENDING):
        vehicle = Vehicle.objects.create(
            year=2022,
            first_registration_date=timezone.now().date(),
            model=self.model,
            color='블랙',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=10000,
            region='서울'
        )
        Auction.objects.create(vehicle=vehicle, status=auction_status)
        return vehicle

    def test_approve_auction_success(self):
        vehicle = self._create_vehicle(auction_status=Auction.Status.PENDING)
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(f'/api/auctions/{vehicle.id}/approve/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        vehicle.refresh_from_db()
        self.assertEqual(vehicle.auction.status, Auction.Status.AUCTION_ACTIVE)
        self.assertIsNotNone(vehicle.auction.start_time)
        self.assertIsNotNone(vehicle.auction.end_time)

        expected_end = vehicle.auction.start_time + timedelta(hours=48)
        time_diff = abs((vehicle.auction.end_time - expected_end).total_seconds())
        self.assertLess(time_diff, 60)  # 1분 이내 오차

    def test_approve_auction_requires_admin(self):
        vehicle = self._create_vehicle(auction_status=Auction.Status.PENDING)
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.post(f'/api/auctions/{vehicle.id}/approve/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        vehicle.refresh_from_db()
        self.assertEqual(vehicle.auction.status, Auction.Status.PENDING)

    def test_approve_auction_invalid_status(self):
        vehicle = self._create_vehicle(auction_status=Auction.Status.AUCTION_ACTIVE)
        vehicle.auction.start_time = timezone.now()
        vehicle.auction.end_time = timezone.now() + timedelta(hours=24)
        vehicle.auction.save()

        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(f'/api/auctions/{vehicle.id}/approve/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_approve_creates_auction_history(self):
        vehicle = self._create_vehicle(auction_status=Auction.Status.PENDING)
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(f'/api/auctions/{vehicle.id}/approve/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        history = AuctionHistory.objects.filter(
            vehicle=vehicle,
            action_type=AuctionHistory.ActionType.AUCTION_START
        ).first()

        self.assertIsNotNone(history)
        self.assertEqual(history.user, self.admin_user)


class TransactionCompleteTestCase(TestCase):
    """거래 완료 API 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='test_admin2',
            password='adminpass',
            is_staff=True
        )

        # 테스트 데이터 생성
        self.brand = Brand.objects.create(name='현대')
        self.car_type = CarType.objects.create(brand=self.brand, name='SUV')
        self.model = Model.objects.create(car_type=self.car_type, name='팰리세이드')

    def _create_ended_vehicle(self):
        vehicle = Vehicle.objects.create(
            year=2022,
            first_registration_date=timezone.now().date(),
            model=self.model,
            color='블랙',
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
        return vehicle

    def test_complete_transaction_success(self):
        vehicle = self._create_ended_vehicle()
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(f'/api/auctions/{vehicle.id}/complete/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        vehicle.refresh_from_db()
        self.assertEqual(vehicle.auction.status, Auction.Status.TRANSACTION_COMPLETE)
        self.assertIsNotNone(vehicle.auction.completed_at)

    def test_complete_transaction_invalid_status(self):
        vehicle = Vehicle.objects.create(
            year=2022,
            first_registration_date=timezone.now().date(),
            model=self.model,
            color='블랙',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=10000,
            region='서울'
        )
        Auction.objects.create(
            vehicle=vehicle,
            status=Auction.Status.AUCTION_ACTIVE,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=24)
        )
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(f'/api/auctions/{vehicle.id}/complete/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_complete_creates_auction_history(self):
        vehicle = self._create_ended_vehicle()
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(f'/api/auctions/{vehicle.id}/complete/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        history = AuctionHistory.objects.filter(
            vehicle=vehicle,
            action_type=AuctionHistory.ActionType.TRANSACTION_COMPLETE
        ).first()

        self.assertIsNotNone(history)
        self.assertEqual(history.user, self.admin_user)


class CeleryTaskTestCase(TestCase):
    """Celery 태스크 테스트"""

    def setUp(self):
        self.brand = Brand.objects.create(name='현대')
        self.car_type = CarType.objects.create(brand=self.brand, name='SUV')
        self.model = Model.objects.create(car_type=self.car_type, name='팰리세이드')

    @patch('apps.auctions.tasks.check_expired_auctions.delay')
    def test_periodic_task_scheduled(self, mock_task):
        from apps.auctions.tasks import check_expired_auctions

        # 태스크가 호출 가능한지 확인
        check_expired_auctions.delay()
        mock_task.assert_called_once()

    def test_check_expired_auctions_task(self):

        expired_vehicle = Vehicle.objects.create(
            year=2022,
            first_registration_date=timezone.now().date(),
            model=self.model,
            color='블랙',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=10000,
            region='서울'
        )
        Auction.objects.create(
            vehicle=expired_vehicle,
            status=Auction.Status.AUCTION_ACTIVE,
            start_time=timezone.now() - timedelta(hours=50),
            end_time=timezone.now() - timedelta(hours=2)
        )

        active_vehicle = Vehicle.objects.create(
            year=2023,
            first_registration_date=timezone.now().date(),
            model=self.model,
            color='화이트',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=5000,
            region='부산'
        )
        Auction.objects.create(
            vehicle=active_vehicle,
            status=Auction.Status.AUCTION_ACTIVE,
            start_time=timezone.now() - timedelta(hours=10),
            end_time=timezone.now() + timedelta(hours=38)
        )

        from apps.auctions.tasks import check_expired_auctions
        result = check_expired_auctions()

        expired_vehicle.refresh_from_db()
        active_vehicle.refresh_from_db()

        self.assertEqual(expired_vehicle.auction.status, Auction.Status.AUCTION_ENDED)
        self.assertEqual(active_vehicle.auction.status, Auction.Status.AUCTION_ACTIVE)
        self.assertEqual(result, {'ended_count': 1})