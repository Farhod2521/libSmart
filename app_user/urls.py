from django.urls import path
from .views import (
    RegisterAPIView,
    VerifyCodeAPIView,
    PasswordResetRequestAPIView,
    PasswordResetConfirmAPIView, LoginWithPhoneAPIView, FaceLoginAPIView, CustomerProfileAPIView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
) 
urlpatterns = [
    path('customer/register/', RegisterAPIView.as_view()),
    path('customer/verify/', VerifyCodeAPIView.as_view()),
    path('customer/reset-password/request/', PasswordResetRequestAPIView.as_view()),
    path('customer/reset-password/confirm/', PasswordResetConfirmAPIView.as_view()),
    path('customer/login/', LoginWithPhoneAPIView.as_view()),
    path('customer/face-login/', FaceLoginAPIView.as_view()),
    path('customer/profile/', CustomerProfileAPIView.as_view(), name='customer-profile'),
    path('customer/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]
