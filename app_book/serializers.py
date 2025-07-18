from rest_framework import serializers
from .models import CategoryBook, Book, BookRating


class CategoryBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryBook
        fields = '__all__'


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'



class BookRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookRating
        fields = ['book', 'rating', 'comment']

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Baho 1 dan 5 gacha bo‘lishi kerak.")
        return value
    

class BookListSerializer(serializers.ModelSerializer):
    average_rating = serializers.FloatField(source='avg_rating')

    class Meta:
        model = Book
        fields = ['id', 'title', 'creator', 'subject', 'description', 'language', 'image', 'file', 'average_rating']
