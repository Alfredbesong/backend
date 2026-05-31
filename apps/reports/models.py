from django.conf import settings
from django.db import models


class WasteReport(models.Model):
    class Status(models.TextChoices):
        REPORTED = "reported", "Reported"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="waste_reports")
    description = models.TextField()
    photo = models.ImageField(upload_to="reports/")
    latitude = models.FloatField()
    longitude = models.FloatField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REPORTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.id} - {self.status}"

    @property
    def progress_percent(self) -> int:
        if self.status == self.Status.RESOLVED:
            return 100
        if self.status == self.Status.IN_PROGRESS:
            return 60
        return 20

    @property
    def progress_step(self) -> int:
        if self.status == self.Status.RESOLVED:
            return 3
        if self.status == self.Status.IN_PROGRESS:
            return 2
        return 1


class Confirmation(models.Model):
    report = models.ForeignKey(WasteReport, on_delete=models.CASCADE, related_name="confirmations")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="confirmations")
    is_cleared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Confirmation for {self.report_id}"
