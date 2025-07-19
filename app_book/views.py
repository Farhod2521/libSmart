from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CategoryBook, Book, BookRating
from .serializers import CategoryBookSerializer, BookSerializer, BookRatingSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
import random
from app_user.models import Customer
# ---------- CategoryBook Views ----------

class CategoryBookListAPIView(APIView):
    def get(self, request):
        categories = CategoryBook.objects.all()
        serializer = CategoryBookSerializer(categories, many=True)
        return Response(serializer.data)


class CategoryBookCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CategoryBookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryBookUpdateAPIView(APIView):
    def put(self, request, pk):
        category = get_object_or_404(CategoryBook, pk=pk)
        serializer = CategoryBookSerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryBookDeleteAPIView(APIView):
    def delete(self, request, pk):
        category = get_object_or_404(CategoryBook, pk=pk)
        category.delete()
        return Response({"detail": "Deleted"}, status=status.HTTP_204_NO_CONTENT)


# ---------- Book Views ----------

class BookListAPIView(APIView):
    def get(self, request):
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)


class BookCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookUpdateAPIView(APIView):
    def put(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        serializer = BookSerializer(book, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookDeleteAPIView(APIView):
    def delete(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        book.delete()
        return Response({"detail": "Deleted"}, status=status.HTTP_204_NO_CONTENT)


class RandomBookListAPIView(APIView):
    def get(self, request):
        books = list(Book.objects.all())
        random_books = random.sample(books, min(len(books), 20))  # 20 tadan kam bo‘lsa, mavjudlar chiqadi
        serializer = BookSerializer(random_books, many=True)
        return Response(serializer.data)
    





##############################  BOOK RATING ###################################
class BookRatingCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Foydalanuvchi Customer ekanligini tekshiramiz
        try:
            customer = user.customer_profile
        except Customer.DoesNotExist:
            return Response({'error': 'Faqat mijozlar baho bera oladi.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = BookRatingSerializer(data=request.data)
        if serializer.is_valid():
            book = serializer.validated_data['book']

            # Oldin baho berilganmi, tekshiramiz
            if BookRating.objects.filter(customer=customer, book=book).exists():
                return Response({'error': 'Siz bu kitobga allaqachon baho bergansiz.'}, status=status.HTTP_400_BAD_REQUEST)

            serializer.save(customer=customer)
            return Response({'message': 'Baho muvaffaqiyatli qo‘shildi.'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)