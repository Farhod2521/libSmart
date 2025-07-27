from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from app_book.models import SearchHistory
from app_user.serializers import SearchHistorySerializer

class SearchHistoryListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        customer = getattr(request.user, "customer_profile", None)
        if not customer:
            return Response({"detail": "Foydalanuvchi profili topilmadi"}, status=400)

        queryset = SearchHistory.objects.filter(customer=customer).order_by('-searched_at')
        serializer = SearchHistorySerializer(queryset, many=True)
        return Response(serializer.data)
