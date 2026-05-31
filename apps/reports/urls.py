from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ConfirmationCreateView, WasteReportViewSet

router = DefaultRouter()
router.register(r"reports", WasteReportViewSet, basename="reports")

urlpatterns = [
    path("", include(router.urls)),
    path("confirm/", ConfirmationCreateView.as_view(), name="confirm-report"),
]
