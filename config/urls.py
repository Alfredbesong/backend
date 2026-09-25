from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("dashboard/", include("apps.reports.dashboard_urls")),
    path("api/", include("apps.reports.urls")),
    path("api/", include("apps.users.urls")),
]

# The MVP dashboard links directly to uploaded report and profile images.
# Render stores these files on the configured persistent disk when using a paid service.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
