from django.contrib import admin

from .models import Confirmation, WasteReport
from .notification_service import send_report_status_notification


@admin.register(WasteReport)
class WasteReportAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("description", "user__username")

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change and obj.pk:
            previous_status = (
                WasteReport.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
            )

        super().save_model(request, obj, form, change)

        if previous_status is not None and previous_status != obj.status:
            send_report_status_notification(obj)


@admin.register(Confirmation)
class ConfirmationAdmin(admin.ModelAdmin):
    list_display = ("id", "report", "user", "is_cleared", "created_at")
    list_filter = ("is_cleared", "created_at")
