from django.urls import path
from .views import (
    CategoryBookListAPIView, CategoryBookCreateAPIView,
    CategoryBookUpdateAPIView, CategoryBookDeleteAPIView,
    BookListAPIView, BookCreateAPIView,
    BookUpdateAPIView, BookDeleteAPIView,RandomBookListAPIView, BookRatingCreateAPIView, AllBookListAPIView, BookDetailAPIView 
)

urlpatterns = [
    # CategoryBook
    path('category/list/', CategoryBookListAPIView.as_view(), name='categorybook-list'),
    path('category/create/', CategoryBookCreateAPIView.as_view(), name='categorybook-create'),
    path('category/update/<int:pk>/', CategoryBookUpdateAPIView.as_view(), name='categorybook-update'),
    path('category/delete/<int:pk>/', CategoryBookDeleteAPIView.as_view(), name='categorybook-delete'),
    path('books/<int:pk>/', BookDetailAPIView.as_view(), name='book-detail'),

    # Book
    path('book/list/', BookListAPIView.as_view(), name='book-list'),
    path('book/create/', BookCreateAPIView.as_view(), name='book-create'),
    path('book/update/<int:pk>/', BookUpdateAPIView.as_view(), name='book-update'),
    path('book/delete/<int:pk>/', BookDeleteAPIView.as_view(), name='book-delete'),
    path('book/random/', RandomBookListAPIView.as_view(), name='book-delete'),


    path('customer/books/rate/', BookRatingCreateAPIView.as_view(), name='book-rating'),
    path('all-books/', AllBookListAPIView.as_view(), name='book-list'),
]
