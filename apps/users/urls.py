from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import DeleteAccountView, DeviceTokenUpsertView, ProfileView, RegisterView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/me/', ProfileView.as_view(), name='profile'),
    path('auth/me/delete/', DeleteAccountView.as_view(), name='delete-account'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/device-token/', DeviceTokenUpsertView.as_view(), name='device-token'),
]
