from celery import shared_task
from django.utils import timezone


@shared_task
def check_auction_end():
    """경매 종료 시간 체크 (매분 실행) - Phase 8에서 구현"""
    from apps.vehicles.models import Vehicle

    # 경매 종료 시간이 지난 차량들 상태 변경
    ended_vehicles = Vehicle.objects.filter(
        status=Vehicle.Status.AUCTION_ACTIVE,
        auction_end_time__lte=timezone.now()
    )

    updated_count = 0
    for vehicle in ended_vehicles:
        vehicle.status = Vehicle.Status.AUCTION_ENDED
        vehicle.save()
        updated_count += 1

    return f"경매 종료 처리 완료: {updated_count}대"