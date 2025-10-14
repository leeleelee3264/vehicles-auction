from typing import Dict, Any, Optional, List
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from apps.vehicles.models import Vehicle
from apps.auctions.models import Auction, AuctionHistory
from rest_framework.exceptions import NotFound

User = get_user_model()


class AuctionService:

    @transaction.atomic
    def approve_auction(self, vehicle_id: int, user: User) -> Vehicle:

        vehicle = Vehicle.objects.select_related('auction').select_for_update().get(id=vehicle_id)
        auction = vehicle.auction

        auction.approve()

        AuctionHistory.objects.create(
            vehicle=vehicle,
            user=user,
            action_type=AuctionHistory.ActionType.AUCTION_START
        )

        return vehicle

    @transaction.atomic
    def complete_transaction(self, vehicle_id: int, user: User) -> Vehicle:

        vehicle = Vehicle.objects.select_related('auction').select_for_update().get(id=vehicle_id)
        auction = vehicle.auction

        auction.complete()

        AuctionHistory.objects.create(
            vehicle=vehicle,
            user=user,
            action_type=AuctionHistory.ActionType.TRANSACTION_COMPLETE
        )

        return vehicle

    def check_and_end_expired_auctions(self) -> Dict[str, int]:
        """만료된 경매 자동 종료"""
        now = timezone.now()

        # 종료 시간이 지난 경매진행 경매 조회
        expired_auctions = Auction.objects.filter(
            status=Auction.Status.AUCTION_ACTIVE,
            end_time__lte=now
        ).select_related('vehicle').select_for_update()

        ended_count = 0

        with transaction.atomic():
            for auction in expired_auctions:
                # 상태를 경매종료로 변경
                auction.status = Auction.Status.AUCTION_ENDED
                auction.save()

                # 히스토리 생성 (시스템 사용자로)
                system_user, _ = User.objects.get_or_create(
                    username='system',
                    defaults={'is_active': False}
                )

                AuctionHistory.objects.create(
                    vehicle=auction.vehicle,
                    user=system_user,
                    action_type=AuctionHistory.ActionType.AUCTION_END
                )

                ended_count += 1

        return {'ended_count': ended_count}