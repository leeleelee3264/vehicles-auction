from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from apps.vehicles.models import Brand, CarType, Model, Vehicle
from apps.auctions.models import Auction


class TestAuctionModel(TestCase):
    """경매 모델 테스트"""

    def setUp(self):
        brand = Brand.objects.create(name="현대")
        car_type = CarType.objects.create(brand=brand, name="SUV")
        model = Model.objects.create(car_type=car_type, name="팰리세이드")

        self.vehicle = Vehicle.objects.create(
            model=model,
            year=2023,
            first_registration_date=timezone.now().date() - timedelta(days=30),
            color='검정',
            fuel_type=Vehicle.FuelType.GASOLINE,
            transmission=Vehicle.Transmission.AUTO,
            mileage=5000,
            region='서울'
        )

    def test_create_auction_with_vehicle(self):
        auction = Auction.objects.create(vehicle=self.vehicle)

        self.assertIsNotNone(auction.id)
        self.assertEqual(auction.status, Auction.Status.PENDING)
        self.assertEqual(auction.vehicle, self.vehicle)

    def test_auction_default_status_is_pending(self):
        auction = Auction.objects.create(vehicle=self.vehicle)
        self.assertEqual(auction.status, Auction.Status.PENDING)

    def test_approve_auction_success(self):
        auction = Auction.objects.create(vehicle=self.vehicle)
        auction.approve()

        self.assertEqual(auction.status, Auction.Status.AUCTION_ACTIVE)
        self.assertIsNotNone(auction.start_time)
        self.assertIsNotNone(auction.end_time)

        expected_end = auction.start_time + timedelta(hours=48)
        time_diff = abs((auction.end_time - expected_end).total_seconds())
        self.assertLess(time_diff, 60)

    def test_approve_auction_invalid_status(self):
        auction = Auction.objects.create(vehicle=self.vehicle)
        auction.status = Auction.Status.AUCTION_ACTIVE
        auction.save()

        with self.assertRaises(ValidationError) as ctx:
            auction.approve()

        self.assertIn("승인대기 상태만", str(ctx.exception))

    def test_complete_transaction_success(self):
        auction = Auction.objects.create(vehicle=self.vehicle)
        auction.status = Auction.Status.AUCTION_ENDED
        auction.save()

        auction.complete()

        self.assertEqual(auction.status, Auction.Status.TRANSACTION_COMPLETE)
        self.assertIsNotNone(auction.completed_at)

    def test_complete_transaction_invalid_status(self):
        auction = Auction.objects.create(vehicle=self.vehicle)

        with self.assertRaises(ValidationError) as ctx:
            auction.complete()

        self.assertIn("경매종료 상태만", str(ctx.exception))

    def test_remaining_seconds_calculation(self):
        auction = Auction.objects.create(vehicle=self.vehicle)
        auction.status = Auction.Status.AUCTION_ACTIVE
        auction.start_time = timezone.now()
        auction.end_time = timezone.now() + timedelta(hours=1)
        auction.save()

        remaining = auction.remaining_seconds
        self.assertGreater(remaining, 3500)
        self.assertLess(remaining, 3700)

    def test_remaining_seconds_for_non_active_auction(self):
        auction = Auction.objects.create(vehicle=self.vehicle)
        self.assertEqual(auction.remaining_seconds, 0)

    def test_one_to_one_relationship_with_vehicle(self):
        auction = Auction.objects.create(vehicle=self.vehicle)

        self.assertEqual(self.vehicle.auction, auction)
        self.assertEqual(auction.vehicle, self.vehicle)