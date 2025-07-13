from rest_framework import serializers
from .models import CategoryBook, Book


class CategoryBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryBook
        fields = '__all__'


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'
