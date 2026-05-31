from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView
from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied as ApiPermissionDenied
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from .models import WasteReport
from .notification_service import send_report_status_notification
from .serializers import (
    ConfirmationSerializer,
    WasteReportCreateSerializer,
    WasteReportReadSerializer,
    WasteReportStatusSerializer,
)


class AdminOnlyMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('reports-dashboard-login')
        if not (request.user.is_staff or request.user.role == 'admin'):
            raise DjangoPermissionDenied('Only admin users can access the dashboard.')
        return super().dispatch(request, *args, **kwargs)


class AdminDashboardLoginView(LoginView):
    template_name = 'reports/dashboard_login.html'
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('reports-dashboard-home')

    def form_valid(self, form):
        user = form.get_user()
        if not (user.is_staff or user.role == 'admin'):
            form.add_error(None, 'Only admin accounts can access this dashboard.')
            return self.form_invalid(form)
        return super().form_valid(form)


class AdminDashboardLogoutView(LogoutView):
    next_page = reverse_lazy('reports-dashboard-login')


class AdminDashboardView(AdminOnlyMixin, TemplateView):
    template_name = 'reports/dashboard_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status_filter = self.request.GET.get('status', '').strip()
        queryset = WasteReport.objects.select_related('user').order_by('-updated_at')

        if status_filter in {
            WasteReport.Status.REPORTED,
            WasteReport.Status.IN_PROGRESS,
            WasteReport.Status.RESOLVED,
        }:
            queryset = queryset.filter(status=status_filter)

        summary_rows = WasteReport.objects.values('status').annotate(total=Count('id'))
        summary = {
            WasteReport.Status.REPORTED: 0,
            WasteReport.Status.IN_PROGRESS: 0,
            WasteReport.Status.RESOLVED: 0,
        }
        for row in summary_rows:
            summary[row['status']] = row['total']

        context.update(
            {
                'reports': queryset,
                'selected_status': status_filter,
                'summary': summary,
                'status_choices': WasteReport.Status.choices,
                'total_reports': sum(summary.values()),
            }
        )
        return context


class AdminDashboardStatusUpdateView(AdminOnlyMixin, View):
    def post(self, request, report_id):
        report = get_object_or_404(WasteReport, pk=report_id)
        next_status = request.POST.get('status', '').strip()
        allowed_statuses = {
            WasteReport.Status.IN_PROGRESS,
            WasteReport.Status.RESOLVED,
        }

        if next_status not in allowed_statuses:
            messages.error(request, 'Please choose a valid admin status.')
            return redirect('reports-dashboard-home')

        previous_status = report.status
        if previous_status == next_status:
            messages.info(request, f'Report #{report.id} is already marked {report.get_status_display()}.')
            return redirect('reports-dashboard-home')

        report.status = next_status
        report.save(update_fields=['status', 'updated_at'])
        send_report_status_notification(report)
        messages.success(
            request,
            f'Report #{report.id} updated to {report.get_status_display()}. The user has been notified when a device token is available.',
        )
        return redirect('reports-dashboard-home')


class WasteReportViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'admin':
            return WasteReport.objects.select_related('user').order_by('-created_at')
        return WasteReport.objects.filter(user=user).select_related('user').order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return WasteReportCreateSerializer
        if self.action in {'update', 'partial_update'}:
            return WasteReportStatusSerializer
        return WasteReportReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save()
        output_serializer = WasteReportReadSerializer(report, context=self.get_serializer_context())
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=201, headers=headers)

    def perform_update(self, serializer):
        if not (self.request.user.is_staff or self.request.user.role == 'admin'):
            raise ApiPermissionDenied('Only admin users can update report status.')

        previous_status = serializer.instance.status
        updated_report = serializer.save()

        if previous_status != updated_report.status:
            send_report_status_notification(updated_report)

    def destroy(self, request, *args, **kwargs):
        report = get_object_or_404(WasteReport.objects.select_related('user'), pk=kwargs['pk'])
        user = request.user
        if report.user != user and not (user.is_staff or user.role == 'admin'):
            raise ApiPermissionDenied('You can only delete your own report.')

        self.perform_destroy(report)
        return Response(status=204)


class ConfirmationCreateView(CreateAPIView):
    serializer_class = ConfirmationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        report = serializer.validated_data['report']
        if report.user != self.request.user and not self.request.user.is_staff:
            raise ApiPermissionDenied('You can only confirm your own report.')
        serializer.save(user=self.request.user)
