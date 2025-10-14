# 차량 경매 시스템

차량 등록 및 경매 관리를 위한 RESTful API 서비스입니다.

## 프로젝트 개요

- 차량 등록 및 조회
- 브랜드/차종/모델 기반 계층적 필터링
- 경매 상태 관리 (승인대기 → 경매진행 → 경매종료 → 거래완료)
- JWT 기반 인증
- Celery를 통한 경매 자동 종료 처리

## 기술 스택

- **Backend**: Django, Django REST Framework
- **Database**: MySQL 
- **Queue**: Redis 
- **Task Queue**: Celery 
- **Authentication**: JWT 

## 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone git@github.com:PRNDcompany/test-leeleelee3264.git
cd test-leeleelee3264

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate 

# 패키지 설치
pip install -r requirements.txt
```

### 2. 인프라 시작 (Docker)

```bash
# MySQL, Redis 컨테이너 시작
docker-compose up -d

# 컨테이너 상태 확인
docker-compose ps
```

### 3. 데이터베이스 초기화

```bash
# 마이그레이션 실행
python manage.py migrate

# 브랜드/차종/모델 데이터 임포트
python scripts/import_brands.py

# 더미 차량 데이터 생성 
# 100대 생성 
python scripts/generate_dummy.py
```

### 4. 서비스 실행

**3개의 터미널**에서 각각 실행합니다 (가상환경 활성화 상태):

```bash
# 터미널 1: Django 서버
python manage.py runserver

# 터미널 2: Celery Worker
celery -A config worker -l info

# 터미널 3: Celery Beat (경매 자동 종료)
celery -A config beat -l info
```

서버 실행 확인: http://localhost:8000

---

## API 명세 및 테스트

### 기본 정보

- **Base URL**: `http://localhost:8000`
- **인증 방식**: JWT Bearer Token

### 테스트용 계정

더미 데이터 생성 시 자동으로 생성되는 계정:

- **일반 사용자**: `demo_user` / `demo123!@#`
- **관리자**: `admin` / `admin123!@#`

---

## 1. 인증 API

### 로그인

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123!@#"
  }'
```

**응답 예시:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@auction.com",
    "is_staff": true
  }
}
```

**[중요]** 이후 API 요청 시 `access` 토큰을 `Authorization: Bearer <token>` 헤더에 포함시켜야 합니다.

---

## 2. 차량 API

### 2-1. 차량 목록 조회

```bash
# 기본 조회 (모든 차량)
curl -X GET http://localhost:8000/api/vehicles/ \
  -H "Authorization: Bearer <access_token>"

# 브랜드 필터링 
curl -X GET "http://localhost:8000/api/vehicles/?brand=3" \
  -H "Authorization: Bearer <access_token>"

# 브랜드 + 차종 필터링 
curl -X GET "http://localhost:8000/api/vehicles/?brand=3&car_type=81" \
  -H "Authorization: Bearer <access_token>"

# 브랜드 + 차종 + 모델 필터링 
curl -X GET "http://localhost:8000/api/vehicles/?brand=3&car_type=81&model=249" \
  -H "Authorization: Bearer <access_token>"

# 정렬 (경매시작 최신순)
curl -X GET "http://localhost:8000/api/vehicles/?sort=-auction__start_time" \
  -H "Authorization: Bearer <access_token>"

# 정렬 (경매시작 오래된순)
curl -X GET "http://localhost:8000/api/vehicles/?sort=auction__start_time" \
  -H "Authorization: Bearer <access_token>"
  
# 페이지네이션 
curl -X GET "http://localhost:8000/api/vehicles/?page=2page_size=10" \
  -H "Authorization: Bearer <access_token>"

```

**쿼리 파라미터:**
- `brand`: 브랜드 ID 
- `car_type`: 차종 ID 
- `model`: 모델 ID 
- `sort`: 정렬 기준 (`-auction__start_time` 또는 `auction__start_time`)
- 페이지네이션: `page` , `page_size` (기본 20)

**응답 예시:**
```json
{
    "count": 87,
    "next": "http://localhost:8000/api/vehicles/?page=3&page_size=10",
    "previous": "http://localhost:8000/api/vehicles/?page_size=10",
    "results": [
        {
            "id": 75,
            "brand_name": "시트로엥·DS",
            "model_name": "XM (89년~00년)",
            "year": 2014,
            "mileage": 117588,
            "fuel_type": "diesel",
            "status": "AUCTION_ACTIVE",
            "auction_start_time": "2025-10-14T05:10:12.486173+09:00",
            "auction_end_time": "2025-10-16T05:10:12.486173+09:00",
            "remaining_seconds": 114778,
            "thumbnail_image": "http://localhost:8000/media/vehicle_images/2025/10/14/vehicle_75_img_1_jHDI9t6.jpg",
            "region": "강원"
        },
      ... 
    ]
}
```

### 2-2. 차량 상세 조회

```bash
curl -X GET http://localhost:8000/api/vehicles/1/ \
  -H "Authorization: Bearer <access_token>"
```

**응답 예시:**
```json
{
    "id": 1,
    "brand": {
        "id": 25,
        "name": "르노"
    },
    "car_type": {
        "id": 533,
        "name": "라구나"
    },
    "model": {
        "id": 1103,
        "name": "라구나 (93년~15년)"
    },
    "year": 2019,
    "first_registration_date": "2020-03-03",
    "color": "베이지",
    "fuel_type": "gasoline",
    "transmission": "auto",
    "mileage": 50481,
    "region": "인천",
    "status": "TRANSACTION_COMPLETE",
    "auction_start_time": "2025-10-03T21:10:10.089939+09:00",
    "auction_end_time": "2025-10-05T21:10:10.089939+09:00",
    "remaining_seconds": 0,
    "images": [
        {
            "id": 1,
            "image": "http://localhost:8000/media/vehicle_images/2025/10/14/vehicle_1_img_1_OUzaUQa.jpg",
            "is_primary": true
        },
        {
            "id": 2,
            "image": "http://localhost:8000/media/vehicle_images/2025/10/14/vehicle_1_img_2_ikDUhUF.jpg",
            "is_primary": false
        },
        {
            "id": 3,
            "image": "http://localhost:8000/media/vehicle_images/2025/10/14/vehicle_1_img_3_cmQvCIo.jpg",
            "is_primary": false
        },
        {
            "id": 4,
            "image": "http://localhost:8000/media/vehicle_images/2025/10/14/vehicle_1_img_4_wpfoFNZ.jpg",
            "is_primary": false
        },
        {
            "id": 5,
            "image": "http://localhost:8000/media/vehicle_images/2025/10/14/vehicle_1_img_5_5O1AWda.jpg",
            "is_primary": false
        }
    ]
}
```

### 2-3. 필터 트리 조회

브랜드 → 차종 → 모델 계층 구조와 각 항목의 차량 수를 반환합니다.

```bash
curl -X GET http://localhost:8000/api/vehicles/filters/ \
  -H "Authorization: Bearer <access_token>"
```

**응답 예시:**
```json
{
   "brands": [
       {
            "id": 1,
            "name": "현대",
            "count": 7,
            "car_types": [
                {
                    "id": 1,
                    "name": "i30",
                    "count": 0,
                    "models": [
                        {
                            "id": 1,
                            "name": "i30 (PD) (16년~20년)",
                            "count": 0
                        },
                        {
                            "id": 2,
                            "name": "더 뉴 i30 (15년~16년)",
                            "count": 0
                        },
                        {
                            "id": 3,
                            "name": "i30(신형) (11년~15년)",
                            "count": 0
                        },
                        {
                            "id": 4,
                            "name": "i30 cw (08년~11년)",
                            "count": 0
                        },
                        {
                            "id": 5,
                            "name": "i30 (07년~11년)",
                            "count": 0
                        }
                    ]
                },
              ...
}
```

### 2-4. 차량 등록

```bash
curl -X POST http://localhost:8000/api/vehicles/create/ \
  -H "Authorization: Bearer <access_token>" \
  -F "model_id=1" \
  -F "year=2023" \
  -F "first_registration_date=2023-03-15" \
  -F "color=화이트" \
  -F "fuel_type=gasoline" \
  -F "transmission=auto" \
  -F "mileage=12000" \
  -F "region=서울" \
  -F "images=@/path/to/image1.jpg" \
  -F "images=@/path/to/image2.jpg" \
  -F "images=@/path/to/image3.jpg"
```

**필수 필드:**
- `model_id`: 모델 ID (정수)
- `year`: 연식 (정수, 현재 년도 이하)
- `first_registration_date`: 최초등록일 (YYYY-MM-DD 형식)
- `color`: 색상 (문자열)
- `fuel_type`: 연료타입 (`lpg`, `gasoline`, `diesel`, `hybrid`, `electric`, `bifuel`)
- `transmission`: 변속기 (`auto`, `manual`)
- `mileage`: 주행거리 (정수, 0 이상)
- `region`: 지역 (문자열)
- `images`: 이미지 파일 (1개 이상)

**응답**: 차량 상세 정보 반환 (상태: `PENDING`)

---

## 3. 경매 API

**[주의]** 경매 API는 **관리자 권한**이 필요합니다. `admin` 계정으로 로그인하여 토큰을 발급받아야 합니다.

### 3-1. 경매 승인

승인대기(`PENDING`) 상태의 차량을 경매진행(`AUCTION_ACTIVE`) 상태로 변경합니다.
경매 시작 시간은 현재 시각, 종료 시간은 48시간 후로 설정됩니다.

```bash
curl -X POST http://localhost:8000/api/auctions/3/approve/ \
  -H "Authorization: Bearer <admin_access_token>"
```

**응답**: 차량 상세 정보 반환 (상태: `AUCTION_ACTIVE`)

### 3-2. 거래 완료

경매종료(`AUCTION_ENDED`) 상태의 차량을 거래완료(`TRANSACTION_COMPLETE`) 상태로 변경합니다.

```bash
curl -X POST http://localhost:8000/api/auctions/18/complete/ \
  -H "Authorization: Bearer <admin_access_token>"
```

**응답**: 차량 상세 정보 반환 (상태: `TRANSACTION_COMPLETE`)

---

## 경매 상태 흐름

```
PENDING (승인대기)
    ↓ [관리자 승인]
AUCTION_ACTIVE (경매진행)
    ↓ [48시간 경과 - Celery 자동 처리]
AUCTION_ENDED (경매종료)
    ↓ [관리자 거래완료 처리]
TRANSACTION_COMPLETE (거래완료)
```

---

## 테스트 실행

```bash

python manage.py test apps.vehicles
python manage.py test apps.auctions
python manage.py test apps.accounts

```

---

## 프로젝트 구조

```
vehicle-auction/
├── apps/
│   ├── accounts/       # 인증
│   ├── vehicles/       # 차량 관리
│   ├── auctions/       # 경매 관리
│   └── common/         # 공통 모듈
├── config/             # 프로젝트 설정
├── scripts/            # 데이터 임포트 스크립트
├── docker-compose.yml  # Docker 구성
├── requirements.txt    # Python 패키지
└── README.md
```

