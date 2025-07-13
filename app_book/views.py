from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CategoryBook, Book
from .serializers import CategoryBookSerializer, BookSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

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
