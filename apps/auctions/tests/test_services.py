from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from apps.vehicles.models import Brand, CarType, Model, Vehicle
from apps.auctions.models import Auction, AuctionHistory
from apps.auctions.services import AuctionService

User = get_user_model()


class AuctionServiceTestCase(TestCase):
    """경매 서비스 기본 테스트"""

    def setUp(self):
        self.service = AuctionService()

        # 사용자 생성
        self.admin_user = User.objects.create_user(
            username='test_admin',
            password='adminpass',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='test_user',
            password='userpass'
        )

        # 테스트 데이터 생성
        self.brand = Brand.objects.create(name='현대')
        self.car_type = CarType.objects.create(brand=self.brand, name='SUV')
        self.model = Model.objects.create(car_type=self.car_type, name='팰리세이드')

    def _create_vehicle_with_auction(self, auction_status=Auction.Status.PENDING):
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

        if auction_status == Auction.Status.AUCTION_ACTIVE:
            auction = Auction.objects.create(
                vehicle=vehicle,
                status=auction_status,
                start_time=timezone.now(),
                end_time=timezone.now() + timedelta(hours=48)
            )
        elif auction_status == Auction.Status.AUCTION_ENDED:
            auction = Auction.objects.create(
                vehicle=vehicle,
                status=auction_status,
                start_time=timezone.now() - timedelta(hours=50),
                end_time=timezone.now() - timedelta(hours=2)
            )
        else:
            auction = Auction.objects.create(vehicle=vehicle, status=auction_status)

        return vehicle

    def test_approve_auction_success_by_admin(self):
        vehicle = self._create_vehicle_with_auction(Auction.Status.PENDING)
        initial_history_count = AuctionHistory.objects.count()

        result_vehicle = self.service.approve_auction(vehicle.id, self.admin_user)

        self.assertEqual(result_vehicle.id, vehicle.id)
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.auction.status, Auction.Status.AUCTION_ACTIVE)
        self.assertIsNotNone(vehicle.auction.start_time)
        self.assertIsNotNone(vehicle.auction.end_time)

        expected_end = vehicle.auction.start_time + timedelta(hours=48)
        time_diff = abs((vehicle.auction.end_time - expected_end).total_seconds())
        self.assertLess(time_diff, 60)

        self.assertEqual(AuctionHistory.objects.count(), initial_history_count + 1)
        history = AuctionHistory.objects.filter(
            vehicle=vehicle,
            action_type=AuctionHistory.ActionType.AUCTION_START
        ).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.user, self.admin_user)

    def test_approve_auction_fails_for_nonexistent_vehicle(self):
        with self.assertRaises(Vehicle.DoesNotExist):
            self.service.approve_auction(9999, self.admin_user)

    def test_approve_auction_fails_for_already_active_auction(self):
        vehicle = self._create_vehicle_with_auction(Auction.Status.AUCTION_ACTIVE)

        with self.assertRaises(ValidationError) as ctx:
            self.service.approve_auction(vehicle.id, self.admin_user)

        self.assertIn("승인대기 상태만", str(ctx.exception))

    def test_complete_transaction_success_by_admin(self):
        vehicle = self._create_vehicle_with_auction(Auction.Status.AUCTION_ENDED)
        initial_history_count = AuctionHistory.objects.count()

        result_vehicle = self.service.complete_transaction(vehicle.id, self.admin_user)

        self.assertEqual(result_vehicle.id, vehicle.id)
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.auction.status, Auction.Status.TRANSACTION_COMPLETE)
        self.assertIsNotNone(vehicle.auction.completed_at)

        self.assertEqual(AuctionHistory.objects.count(), initial_history_count + 1)
        history = AuctionHistory.objects.filter(
            vehicle=vehicle,
            action_type=AuctionHistory.ActionType.TRANSACTION_COMPLETE
        ).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.user, self.admin_user)

    def test_complete_transaction_fails_for_nonexistent_vehicle(self):
        with self.assertRaises(Vehicle.DoesNotExist):
            self.service.complete_transaction(9999, self.admin_user)

    def test_complete_transaction_fails_for_wrong_status(self):
        vehicle = self._create_vehicle_with_auction(Auction.Status.AUCTION_ACTIVE)

        with self.assertRaises(ValidationError) as ctx:
            self.service.complete_transaction(vehicle.id, self.admin_user)

        self.assertIn("경매종료 상태만", str(ctx.exception))

    def test_check_and_end_expired_auctions_success(self):
        # 만료된 경매 2개 생성
        expired_vehicle1 = Vehicle.objects.create(
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
            vehicle=expired_vehicle1,
            status=Auction.Status.AUCTION_ACTIVE,
            start_time=timezone.now() - timedelta(hours=50),
            end_time=timezone.now() - timedelta(hours=2)
        )

        expired_vehicle2 = Vehicle.objects.create(
            year=2023,
            first_registration_date=timezone.now().date(),
            model=self.model,
            color='화이트',
            fuel_type=Vehicle.FuelType.DIESEL,
            transmission=Vehicle.Transmission.AUTO,
            mileage=5000,
            region='부산'
        )
        Auction.objects.create(
            vehicle=expired_vehicle2,
            status=Auction.Status.AUCTION_ACTIVE,
            start_time=timezone.now() - timedelta(hours=49),
            end_time=timezone.now() - timedelta(hours=1)
        )

        # 진행중인 경매 1개 (종료 시간 전)
        active_vehicle = Vehicle.objects.create(
            year=2023,
            first_registration_date=timezone.now().date(),
            model=self.model,
            color='그레이',
            fuel_type=Vehicle.FuelType.HYBRID,
            transmission=Vehicle.Transmission.AUTO,
            mileage=3000,
            region='대구'
        )
        Auction.objects.create(
            vehicle=active_vehicle,
            status=Auction.Status.AUCTION_ACTIVE,
            start_time=timezone.now() - timedelta(hours=10),
            end_time=timezone.now() + timedelta(hours=38)
        )

        initial_history_count = AuctionHistory.objects.count()

        # 만료 경매 종료 실행
        result = self.service.check_and_end_expired_auctions()

        # 결과 확인
        self.assertEqual(result['ended_count'], 2)

        # 만료된 경매들이 종료 상태로 변경되었는지 확인
        expired_vehicle1.refresh_from_db()
        expired_vehicle2.refresh_from_db()
        active_vehicle.refresh_from_db()

        self.assertEqual(expired_vehicle1.auction.status, Auction.Status.AUCTION_ENDED)
        self.assertEqual(expired_vehicle2.auction.status, Auction.Status.AUCTION_ENDED)
        self.assertEqual(active_vehicle.auction.status, Auction.Status.AUCTION_ACTIVE)

        # 히스토리 생성 확인 (2개)
        self.assertEqual(AuctionHistory.objects.count(), initial_history_count + 2)

        # system 사용자 생성 확인
        system_user = User.objects.filter(username='system').first()
        self.assertIsNotNone(system_user)
        self.assertFalse(system_user.is_active)

        # 히스토리 사용자가 system인지 확인
        histories = AuctionHistory.objects.filter(
            action_type=AuctionHistory.ActionType.AUCTION_END
        ).order_by('-created_at')[:2]

        for history in histories:
            self.assertEqual(history.user, system_user)

    def test_check_and_end_expired_auctions_with_no_expired(self):
        # 진행중인 경매만 생성
        active_vehicle = self._create_vehicle_with_auction(Auction.Status.AUCTION_ACTIVE)

        result = self.service.check_and_end_expired_auctions()

        # 종료된 경매 없음
        self.assertEqual(result['ended_count'], 0)

        # 상태 변경 없음
        active_vehicle.refresh_from_db()
        self.assertEqual(active_vehicle.auction.status, Auction.Status.AUCTION_ACTIVE)


class AuctionServiceTransactionTestCase(TransactionTestCase):
    """경매 서비스 트랜잭션 테스트"""

    def setUp(self):
        self.service = AuctionService()

        self.admin_user = User.objects.create_user(
            username='test_admin_tx',
            password='adminpass',
            is_staff=True
        )

        self.brand = Brand.objects.create(name='현대')
        self.car_type = CarType.objects.create(brand=self.brand, name='SUV')
        self.model = Model.objects.create(car_type=self.car_type, name='팰리세이드')

    def test_approve_auction_rollback_on_error(self):
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
        Auction.objects.create(vehicle=vehicle)

        initial_status = vehicle.auction.status
        initial_history_count = AuctionHistory.objects.count()

        vehicle.auction.status = Auction.Status.AUCTION_ACTIVE
        vehicle.auction.save()

        try:
            self.service.approve_auction(vehicle.id, self.admin_user)
        except ValidationError:
            pass

        # 롤백 확인
        vehicle.refresh_from_db()
        self.assertEqual(AuctionHistory.objects.count(), initial_history_count)

    def test_complete_transaction_rollback_on_error(self):
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
            status=Auction.Status.AUCTION_ACTIVE
        )

        initial_status = vehicle.auction.status
        initial_history_count = AuctionHistory.objects.count()

        try:
            self.service.complete_transaction(vehicle.id, self.admin_user)
        except ValidationError:
            pass

        vehicle.refresh_from_db()
        self.assertEqual(vehicle.auction.status, initial_status)
        self.assertEqual(AuctionHistory.objects.count(), initial_history_count)
