from rest_framework.pagination import PageNumberPagination


class VehicleListPagination(PageNumberPagination):
    """차량 목록 페이지네이션"""
    page_size = 20  # 기본 페이지 사이즈
    page_size_query_param = 'page_size'  # 클라이언트가 페이지 사이즈 조정 가능
    max_page_size = 100  # 최대 페이지 사이즈 제한