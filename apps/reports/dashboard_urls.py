from django.urls import path

from .views import (
    AdminDashboardLoginView,
    AdminDashboardLogoutView,
    AdminDashboardStatusUpdateView,
    AdminDashboardView,
)

urlpatterns = [
    path('login/', AdminDashboardLoginView.as_view(), name='reports-dashboard-login'),
    path('logout/', AdminDashboardLogoutView.as_view(), name='reports-dashboard-logout'),
    path('', AdminDashboardView.as_view(), name='reports-dashboard-home'),
    path('reports/<int:report_id>/status/', AdminDashboardStatusUpdateView.as_view(), name='reports-dashboard-status'),
]
