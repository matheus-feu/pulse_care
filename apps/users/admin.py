from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'full_name', 'role', 'license_number', 'specialty', 'is_active', 'is_staff']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name', 'license_number']
    ordering = ['first_name', 'last_name']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Professional Info', {
            'fields': ('role', 'license_number', 'specialty', 'phone', 'avatar'),
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Professional Info', {
            'fields': ('email', 'first_name', 'last_name', 'role', 'license_number', 'specialty', 'phone'),
        }),
    )
