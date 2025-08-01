from django.urls import path
from .views import (
    RegisterAPIView,
    VerifyCodeAPIView,
    PasswordResetRequestAPIView,
    PasswordResetConfirmAPIView, LoginWithPhoneAPIView, FaceLoginAPIView, CustomerProfileAPIView, NotificationListAPIView,
    CustomerProfileUpdateAPIView, LoginWithPhoneAdminAPIView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
) 
from .VIEW.searchview    import SearchHistoryListAPIView
urlpatterns = [
    path('customer/register/', RegisterAPIView.as_view()),
    path('customer/verify/', VerifyCodeAPIView.as_view()),
    path('customer/reset-password/request/', PasswordResetRequestAPIView.as_view()),
    path('customer/reset-password/confirm/', PasswordResetConfirmAPIView.as_view()),
    path('customer/login/', LoginWithPhoneAPIView.as_view()),
    path('customer/face-login/', FaceLoginAPIView.as_view()),
    path('customer/profile/', CustomerProfileAPIView.as_view(), name='customer-profile'),
    path('customer/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('customer/search-history/', SearchHistoryListAPIView.as_view(), name='search-history-list'),

    path('customer/notifications/', NotificationListAPIView.as_view(), name='notification-list'),
    path('customer/profile-update/', CustomerProfileUpdateAPIView.as_view(), name='customer-profile-update'),
    path('admin/login/', LoginWithPhoneAPIView.as_view()),


]
