from celery import shared_task
from celery.utils.log import get_task_logger
from typing import Dict

logger = get_task_logger(__name__)


@shared_task
def check_expired_auctions() -> Dict[str, int]:

    from apps.auctions.services import AuctionService

    logger.info("경매 만료 확인 태스크 시작")

    service = AuctionService()
    result = service.check_and_end_expired_auctions()

    logger.info(f"경매 만료 확인 완료: {result['ended_count']}개 경매 종료")

    return result
