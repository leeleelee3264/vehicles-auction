#!/usr/bin/env python
"""
차량 더미 데이터를 생성하는 스크립트 (총 20대)

사용법:
    python scripts/generate_dummy.py
"""

import os
import sys
import django
import random
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

# Django 설정
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from django.core.files.base import ContentFile
from PIL import Image
import io
from faker import Faker
from apps.vehicles.models import Vehicle, Brand, CarType, Model, VehicleImage
from apps.auctions.models import Auction

fake = Faker('ko_KR')


class DummyVehicleGenerator:
    """차량 더미 데이터 생성 클래스"""

    # 색상 옵션
    COLORS = [
        '화이트', '블랙', '실버', '그레이', '레드', '블루',
        '네이비', '다크그레이', '화이트펄', '블랙펄', '실버메탈릭',
        '다크블루', '와인', '브라운', '베이지', '옐로우', '그린'
    ]

    # 지역 옵션
    REGIONS = [
        '서울', '경기', '인천', '부산', '대구', '광주', '대전',
        '울산', '세종', '강원', '충북', '충남', '전북', '전남',
        '경북', '경남', '제주'
    ]

    # 연료 타입
    FUEL_TYPES = [
        ('lpg', 0.1),           # 10%
        ('gasoline', 0.4),      # 40%
        ('diesel', 0.25),       # 25%
        ('hybrid', 0.15),       # 15%
        ('electric', 0.08),     # 8%
        ('bifuel', 0.02),       # 2%
    ]

    # 변속기 타입
    TRANSMISSIONS = [
        ('auto', 0.85),         # 85%
        ('manual', 0.15),       # 15%
    ]

    def __init__(self):
        self.created_count = 0
        self.failed_count = 0

    def get_weighted_choice(self, choices):
        """가중치 기반 랜덤 선택"""
        items = [item[0] for item in choices]
        weights = [item[1] for item in choices]
        return random.choices(items, weights=weights)[0]

    def generate_vehicle_image(self, vehicle_id, index):
        """더미 차량 이미지 생성"""
        # 간단한 색상 이미지 생성 (실제로는 실제 이미지를 사용해야 함)
        width, height = 800, 600

        # 랜덤 색상 생성
        colors = [
            (255, 255, 255),  # 화이트
            (0, 0, 0),        # 블랙
            (192, 192, 192),  # 실버
            (128, 128, 128),  # 그레이
            (255, 0, 0),      # 레드
            (0, 0, 255),      # 블루
        ]
        color = random.choice(colors)

        # PIL로 이미지 생성
        image = Image.new('RGB', (width, height), color)

        # 텍스트 추가 (차량 ID와 이미지 번호)
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.load_default()
        except:
            font = None

        text = f"Vehicle #{vehicle_id}\nImage {index}"
        text_color = (255, 255, 255) if sum(color) < 384 else (0, 0, 0)

        # 텍스트를 이미지 중앙에 배치
        if font:
            # 텍스트 크기 계산
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((width - text_width) // 2, (height - text_height) // 2)
            draw.text(position, text, fill=text_color, font=font)
        else:
            draw.text((width//2 - 100, height//2 - 20), text, fill=text_color)

        # 이미지를 바이트로 변환
        img_io = io.BytesIO()
        image.save(img_io, format='JPEG', quality=85)
        img_io.seek(0)

        return ContentFile(img_io.read(), name=f'vehicle_{vehicle_id}_img_{index}.jpg')

    def create_dummy_vehicle(self):
        """더미 차량 1대 생성"""
        try:
            # 브랜드, 차종, 모델 랜덤 선택
            if not Model.objects.exists():
                print("모델 데이터가 없습니다. import_brands.py를 먼저 실행하세요.")
                return False

            # 랜덤 모델 선택
            model = Model.objects.order_by('?').first()

            # 연식 설정 (최근 15년)
            current_year = timezone.now().year
            year = random.randint(current_year - 15, current_year)

            # 최초등록일 설정 (연식 이후)
            if year == current_year:
                # 올해 차량은 최근 날짜
                days_ago = random.randint(1, 180)
            else:
                # 과거 차량은 해당 년도 내 랜덤 날짜
                days_ago = random.randint(
                    (current_year - year) * 365 - 180,
                    (current_year - year) * 365 + 180
                )
            first_registration_date = timezone.now().date() - timedelta(days=days_ago)

            # 주행거리 (연식에 비례)
            years_old = current_year - year
            base_mileage = years_old * random.randint(8000, 15000)
            mileage = max(0, base_mileage + random.randint(-5000, 20000))

            # 차량 생성 (경매 관련 필드 제거)
            vehicle = Vehicle.objects.create(
                year=year,
                first_registration_date=first_registration_date,
                model=model,
                color=random.choice(self.COLORS),
                fuel_type=self.get_weighted_choice(self.FUEL_TYPES),
                transmission=self.get_weighted_choice(self.TRANSMISSIONS),
                mileage=mileage,
                region=random.choice(self.REGIONS)
            )

            # 경매 상태 결정 (가중치 적용)
            status_weights = [
                (Auction.Status.PENDING, 0.2),              # 20% 승인대기
                (Auction.Status.AUCTION_ACTIVE, 0.3),       # 30% 경매진행
                (Auction.Status.AUCTION_ENDED, 0.2),        # 20% 경매종료
                (Auction.Status.TRANSACTION_COMPLETE, 0.3),  # 30% 거래완료
            ]
            status = self.get_weighted_choice(status_weights)

            # 경매 시간 설정 (상태에 따라)
            start_time = None
            end_time = None
            completed_at = None

            if status == Auction.Status.AUCTION_ACTIVE:
                # 경매 진행중: 시작 시간은 최근, 종료는 미래
                hours_ago = random.randint(1, 40)
                start_time = timezone.now() - timedelta(hours=hours_ago)
                end_time = start_time + timedelta(hours=48)

            elif status == Auction.Status.AUCTION_ENDED:
                # 경매 종료: 시작은 과거, 종료도 과거
                days_ago = random.randint(1, 7)
                start_time = timezone.now() - timedelta(days=days_ago, hours=48)
                end_time = start_time + timedelta(hours=48)

            elif status == Auction.Status.TRANSACTION_COMPLETE:
                # 거래 완료: 모든 시간이 과거
                days_ago = random.randint(7, 30)
                start_time = timezone.now() - timedelta(days=days_ago, hours=48)
                end_time = start_time + timedelta(hours=48)
                completed_at = end_time + timedelta(hours=random.randint(1, 24))

            # 경매 생성
            auction = Auction.objects.create(
                vehicle=vehicle,
                status=status,
                start_time=start_time,
                end_time=end_time,
                completed_at=completed_at
            )

            # 차량 이미지 생성 (5-8장)
            image_count = random.randint(5, 8)
            for i in range(image_count):
                image_file = self.generate_vehicle_image(vehicle.id, i + 1)
                VehicleImage.objects.create(
                    vehicle=vehicle,
                    image=image_file,
                    is_primary=(i == 0)  # 첫 번째 이미지를 대표이미지로
                )

            self.created_count += 1

            # 생성 정보 출력
            print(f"차량 생성: {model.car_type.brand.name} {model.car_type.name} {model.name} "
                  f"({year}년식, {auction.status}, {image_count}장 이미지)")

            return True

        except Exception as e:
            self.failed_count += 1
            print(f"차량 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return False

    def generate_vehicles(self, count=20):
        """지정된 수의 차량 생성"""
        print(f"\n {count}대의 더미 차량 생성 시작...")
        print("="*50)

        for i in range(count):
            print(f"\n[{i+1}/{count}] ", end="")
            self.create_dummy_vehicle()

        print("\n" + "="*50)
        print(f" 더미 데이터 생성 완료")
        print(f"  - 성공: {self.created_count}대")
        print(f"  - 실패: {self.failed_count}대")


def main():
    print("="*50)
    print("[INFO] 차량 더미 데이터 생성 스크립트")
    print("="*50)

    # 모델 데이터 체크
    if not Model.objects.exists():
        print("[ERROR] 브랜드/차종/모델 데이터가 없습니다.")
        print("먼저 다음 명령을 실행하세요:")
        print("  python scripts/import_brands.py")
        sys.exit(1)

    vehicle_count = 20

    # 더미 데이터 생성
    generator = DummyVehicleGenerator()
    generator.generate_vehicles(vehicle_count)

    print("\n[SUCCESS] 스크립트 실행 완료")


if __name__ == '__main__':
    main()