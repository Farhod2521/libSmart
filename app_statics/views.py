from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Avg, Sum
from app_book.models import  Book, BookRating
from app_user.models import Customer
import aiohttp
import asyncio
class StatisticsAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    async def get_external_books_count(self):
        url = "https://api.miku.uz/convert/all"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("count", 0)
                return 0

    def get(self, request):
        # Ichki bazadan ma'lumotlar
        total_books = Book.objects.count()
        total_downloads = Book.objects.aggregate(total=Sum('download_count'))['total'] or 0
        total_customers = Customer.objects.count()
        average_rating = BookRating.objects.aggregate(avg=Avg('rating'))['avg'] or 0

        # Tashqi API ma'lumotini olish
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        external_books_count = loop.run_until_complete(self.get_external_books_count())

        total_all_books = total_books + external_books_count

        return Response({
            "total_books": total_all_books,
            "external_books": external_books_count,
            "TOTAL_books": total_all_books,
            "total_downloads": total_downloads,
            "total_customers": total_customers,
            "average_rating": round(average_rating, 2),
        })