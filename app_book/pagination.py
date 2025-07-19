from rest_framework.pagination import PageNumberPagination

class BookPagination(PageNumberPagination):
    page_size = 10  # Har sahifada nechta element bo‘lsin
    page_size_query_param = 'page_size'  # foydalanuvchi o‘zgartirishi uchun
    max_page_size = 100
