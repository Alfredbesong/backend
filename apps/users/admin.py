from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import DeviceToken, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('role', 'phone_number')}),
    )
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')

    def save_model(self, request, obj, form, change):
        if obj.is_staff or obj.is_superuser:
            obj.role = User.Role.ADMIN
        super().save_model(request, obj, form, change)


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'platform', 'is_active', 'updated_at')
    list_filter = ('platform', 'is_active')
    search_fields = ('user__username', 'token')
