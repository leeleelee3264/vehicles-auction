from django.db import models
from django.contrib.auth.models import User


class AuctionHistory(models.Model):
    """경매 이력 모델 (향후 경매 입찰/낙찰 이력 추적용)"""
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        related_name='auction_histories',
        verbose_name='차량'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='auction_histories',
        verbose_name='사용자'
    )
    action_type = models.CharField(
        max_length=20,
        choices=[
            ('BID', '입찰'),
            ('WIN', '낙찰'),
            ('CANCEL', '취소'),
        ],
        verbose_name='액션 타입'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name='금액'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auction_histories'
        verbose_name = '경매 이력'
        verbose_name_plural = '경매 이력 목록'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vehicle} - {self.action_type}"