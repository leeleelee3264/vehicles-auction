from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class Auction(models.Model):
    """경매 모델"""

    class Status(models.TextChoices):
        PENDING = 'PENDING', '승인대기'
        AUCTION_ACTIVE = 'AUCTION_ACTIVE', '경매진행'
        AUCTION_ENDED = 'AUCTION_ENDED', '경매종료'
        TRANSACTION_COMPLETE = 'TRANSACTION_COMPLETE', '거래완료'

    vehicle = models.OneToOneField(
        'vehicles.Vehicle',
        on_delete=models.PROTECT,
        related_name='auction',
        verbose_name='차량'
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='상태'
    )
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='경매시작시간')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='경매종료시간')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='거래완료시간')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'auctions'
        verbose_name = '경매'
        verbose_name_plural = '경매 목록'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'end_time']),
        ]

    def __str__(self):
        return f"{self.vehicle} 경매"

    def approve(self):
        """경매 승인"""
        if self.status != self.Status.PENDING:
            raise ValidationError("승인대기 상태만 경매 승인 가능합니다")

        self.status = self.Status.AUCTION_ACTIVE
        self.start_time = timezone.now()
        self.end_time = timezone.now() + timezone.timedelta(hours=48)
        self.save()

    def complete(self):
        """거래 완료 처리"""
        if self.status != self.Status.AUCTION_ENDED:
            raise ValidationError("경매종료 상태만 거래완료 가능합니다")

        self.status = self.Status.TRANSACTION_COMPLETE
        self.completed_at = timezone.now()
        self.save()

    @property
    def remaining_seconds(self):
        """경매 남은 시간(초)"""
        if self.status != self.Status.AUCTION_ACTIVE:
            return 0

        remaining = self.end_time - timezone.now()
        return max(0, int(remaining.total_seconds()))



class AuctionHistory(models.Model):
    """경매 이력 모델"""

    class ActionType(models.TextChoices):
        AUCTION_START = 'AUCTION_START', '경매시작'
        AUCTION_END = 'AUCTION_END', '경매종료'
        TRANSACTION_COMPLETE = 'TRANSACTION_COMPLETE', '거래완료'

    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        related_name='auction_histories',
        verbose_name='차량'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='auction_histories',
        verbose_name='사용자'
    )
    action_type = models.CharField(
        max_length=20,
        choices=ActionType.choices,
        verbose_name='액션 타입'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auction_histories'
        verbose_name = '경매 이력'
        verbose_name_plural = '경매 이력 목록'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vehicle} - {self.action_type}"