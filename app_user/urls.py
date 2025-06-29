from django.urls import path
from .views import (
    RegisterAPIView,
    VerifyCodeAPIView,
    PasswordResetRequestAPIView,
    PasswordResetConfirmAPIView,LoginWithFaceAPIView
)

urlpatterns = [
    path('customer/register/', RegisterAPIView.as_view()),
    path('customer/verify/', VerifyCodeAPIView.as_view()),
    path('customer/reset-password/request/', PasswordResetRequestAPIView.as_view()),
    path('customer/reset-password/confirm/', PasswordResetConfirmAPIView.as_view()),
    path('customer/login-face/', LoginWithFaceAPIView.as_view()),
]
