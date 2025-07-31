from django.urls import path
from .views import StatisticsAPIView

urlpatterns = [
    path('stats/', StatisticsAPIView.as_view(), name='statistics'),
]
