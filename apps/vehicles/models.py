from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings


class Brand(models.Model):
    """브랜드 모델 (현대, 기아 등)"""
    name = models.CharField(max_length=50, unique=True, verbose_name='브랜드명')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'brands'
        verbose_name = '브랜드'
        verbose_name_plural = '브랜드 목록'
        ordering = ['name']

    def __str__(self):
        return self.name


class CarType(models.Model):
    """차종 모델 (i30, 소나타, 팰리세이드 등)"""
    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name='car_types',
        verbose_name='브랜드'
    )
    name = models.CharField(max_length=50, verbose_name='차종명')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'car_types'
        verbose_name = '차종'
        verbose_name_plural = '차종 목록'
        ordering = ['brand', 'name']
        unique_together = [['brand', 'name']]

    def __str__(self):
        return f"{self.brand.name} {self.name}"


class Model(models.Model):
    """모델 모델 (i30 (PD), 더 뉴 i30, 7세대 소나타 등)"""
    car_type = models.ForeignKey(
        CarType,
        on_delete=models.CASCADE,
        related_name='models',
        verbose_name='차종'
    )
    name = models.CharField(max_length=100, verbose_name='모델명')
    year_start = models.IntegerField(null=True, blank=True, verbose_name='출시년도')
    year_end = models.IntegerField(null=True, blank=True, verbose_name='단종년도')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'models'
        verbose_name = '모델'
        verbose_name_plural = '모델 목록'
        ordering = ['car_type', 'year_start', 'name']
        unique_together = [['car_type', 'name']]

    def __str__(self):
        if self.year_start and self.year_end:
            return f"{self.car_type} {self.name} ({self.year_start}~{self.year_end})"
        elif self.year_start:
            return f"{self.car_type} {self.name} ({self.year_start}~)"
        return f"{self.car_type} {self.name}"


class Vehicle(models.Model):
    """차량 모델"""

    # 연료 타입
    class FuelType(models.TextChoices):
        LPG = 'lpg', 'LPG'
        GASOLINE = 'gasoline', '가솔린'
        DIESEL = 'diesel', '디젤'
        HYBRID = 'hybrid', '하이브리드'
        ELECTRIC = 'electric', '전기'
        BIFUEL = 'bifuel', '바이퓨얼'

    # 변속기
    class Transmission(models.TextChoices):
        AUTO = 'auto', '자동'
        MANUAL = 'manual', '수동'

    # 기본 정보
    year = models.IntegerField(verbose_name='연식')
    first_registration_date = models.DateField(verbose_name='최초등록일')

    # 차량 모델 정보 (외래키)
    model = models.ForeignKey(Model, on_delete=models.PROTECT, verbose_name='모델')

    # 상세 정보
    color = models.CharField(max_length=50, verbose_name='색상')
    fuel_type = models.CharField(
        max_length=20,
        choices=FuelType.choices,
        verbose_name='연료타입'
    )
    transmission = models.CharField(
        max_length=10,
        choices=Transmission.choices,
        verbose_name='변속기'
    )
    mileage = models.PositiveIntegerField(verbose_name='주행거리')
    region = models.CharField(max_length=50, verbose_name='지역')

    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vehicles'
        verbose_name = '차량'
        verbose_name_plural = '차량 목록'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model']),
        ]

    def __str__(self):
        return f"{self.model} ({self.year}년식)"


class VehicleImage(models.Model):
    """차량 이미지 모델"""
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='차량'
    )
    image = models.ImageField(
        upload_to='vehicle_images/%Y/%m/%d/',
        verbose_name='이미지'
    )
    is_primary = models.BooleanField(default=False, verbose_name='대표이미지')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vehicle_images'
        verbose_name = '차량 이미지'
        verbose_name_plural = '차량 이미지 목록'
        ordering = ['-is_primary', 'id']

    def __str__(self):
        return f"{self.vehicle} 이미지"

