from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Avg, Sum
from app_book.models import  Book, BookRating
from app_user.models import Customer

class StatisticsAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        total_books = Book.objects.count()
        total_downloads = Book.objects.aggregate(total=Sum('download_count'))['total'] or 0
        total_customers = Customer.objects.count()
        average_rating = BookRating.objects.aggregate(avg=Avg('rating'))['avg'] or 0

        return Response({
            "total_books": total_books,
            "total_downloads": total_downloads,
            "total_customers": total_customers,
            "average_rating": round(average_rating, 2),
        })
