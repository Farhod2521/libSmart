from rest_framework import serializers
from .models import CategoryBook, Book, BookRating, BookLike


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
        fields = [
            'id',
            'title_uz', 'title_ru', 'title_en',
            'creator_uz', 'creator_ru', 'creator_en',
            'subject_uz', 'subject_ru', 'subject_en',
            'description_uz', 'description_ru', 'description_en',
            'publisher_uz', 'publisher_ru', 'publisher_en',
            'contributor_uz', 'contributor_ru', 'contributor_en',
            'date', 'type', 'format', 'identifier',
            'source_uz', 'source_ru', 'source_en',
            'relation_uz', 'relation_ru', 'relation_en',
            'coverage_uz', 'coverage_ru', 'coverage_en',
            'rights_uz', 'rights_ru', 'rights_en',
            'language',
            'image',
            'file',
            'average_rating'
        ]

class BookRatingDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.user.full_name', read_only=True)

    class Meta:
        model = BookRating
        fields = ['id', 'customer_name', 'rating', 'comment', 'created_at']

class BookDetailSerializer(serializers.ModelSerializer):
    ratings = BookRatingDetailSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    rating_count = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id',
            'title_uz', 'title_ru', 'title_en',
            'creator_uz', 'creator_ru', 'creator_en',
            'subject_uz', 'subject_ru', 'subject_en',
            'description_uz', 'description_ru', 'description_en',
            'publisher_uz', 'publisher_ru', 'publisher_en',
            'contributor_uz', 'contributor_ru', 'contributor_en',
            'date', 'type', 'format', 'identifier',
            'source_uz', 'source_ru', 'source_en',
            'relation_uz', 'relation_ru', 'relation_en',
            'coverage_uz', 'coverage_ru', 'coverage_en',
            'rights_uz', 'rights_ru', 'rights_en',
            'language',
            'image',
            'file',
            'average_rating',
            'rating_count',
            'ratings'
        ]

    def get_rating_count(self, obj):
        return obj.ratings.count()

class BookLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookLike
        fields = ['id', 'book', 'created_at']




