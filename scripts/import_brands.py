#!/usr/bin/env python
"""
브랜드, 차종, 모델 데이터를 엑셀 파일에서 읽어 DB에 임포트하는 스크립트

사용법:
    python scripts/import_brands.py
"""

import os
import sys
import django
from pathlib import Path

# Django 설정
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import pandas as pd
from django.db import transaction
from apps.vehicles.models import Brand, CarType, Model


def import_brand_data():

    excel_path = project_root / '브랜드,차종,모델.xlsx'

    if not excel_path.exists():
        print(f"[ERROR] 엑셀 파일을 찾을 수 없습니다: {excel_path}")
        return False

    try:
        print(f"[INFO] 엑셀 파일 읽는 중: {excel_path}")
        df = pd.read_excel(excel_path)

        # 컬럼명 확인 및 정규화
        print(f"[INFO] 컬럼 확인: {df.columns.tolist()}")

        # 실제 컬럼명으로 작업 (Unnamed: 0은 인덱스이므로 무시)
        # 브랜드, 차종, 모델 컬럼 확인
        expected_columns = ['브랜드', '차종', '모델']
        for col in expected_columns:
            if col not in df.columns:
                print(f"[ERROR] 필수 컬럼 '{col}'이 없습니다.")
                return False

        # 컬럼명을 영문으로 매핑
        df = df.rename(columns={
            '브랜드': 'brand_name',
            '차종': 'car_type_name',
            '모델': 'model_name'
        })

        # NaN 값을 빈 문자열로 대체
        df = df.fillna('')

        # 트랜잭션으로 데이터 저장
        with transaction.atomic():

            # 데이터 임포트 통계
            brands_created = 0
            car_types_created = 0
            models_created = 0

            # 브랜드별로 그룹화하여 처리
            for _, row in df.iterrows():
                brand_name = str(row['brand_name']).strip()
                car_type_name = str(row['car_type_name']).strip()
                model_name = str(row['model_name']).strip()

                if not brand_name:
                    continue

                # 브랜드 생성 또는 가져오기
                brand, created = Brand.objects.get_or_create(
                    name=brand_name
                )
                if created:
                    brands_created += 1

                if not car_type_name:
                    continue

                # 차종 생성 또는 가져오기
                car_type, created = CarType.objects.get_or_create(
                    name=car_type_name,
                    brand=brand
                )
                if created:
                    car_types_created += 1
                    print(f"    [OK] 차종 생성: {brand_name} - {car_type_name}")

                if not model_name:
                    continue

                # 모델 생성 또는 가져오기
                model, created = Model.objects.get_or_create(
                    name=model_name,
                    car_type=car_type
                )
                if created:
                    models_created += 1
                    print(f"      [OK] 모델 생성: {brand_name} - {car_type_name} - {model_name}")

            # 임포트 결과 출력
            print("\n" + "="*50)
            print("[INFO] 임포트 데이터")
            print(f"  - 브랜드: {brands_created}개 생성")
            print(f"  - 차종: {car_types_created}개 생성")
            print(f"  - 모델: {models_created}개 생성")
            print("="*50)

            # 전체 데이터 수 출력
            total_brands = Brand.objects.count()
            total_car_types = CarType.objects.count()
            total_models = Model.objects.count()

            print(f"\n[ INFO] 전체 데이터 현황:")
            print(f"  - 총 브랜드: {total_brands}개")
            print(f"  - 총 차종: {total_car_types}개")
            print(f"  - 총 모델: {total_models}개")

        return True

    except Exception as e:
        print(f"[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("차량 브랜드/차종/모델 데이터 임포트 스크립트")

    import_brand_data()
