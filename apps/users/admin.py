from django.apps import apps as django_apps
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


HIDDEN_ADMIN_MODELS = [
    ('django_celery_beat', 'PeriodicTask'),
    ('django_celery_beat', 'PeriodicTasks'),
    ('django_celery_beat', 'CrontabSchedule'),
    ('django_celery_beat', 'IntervalSchedule'),
    ('django_celery_beat', 'SolarSchedule'),
    ('django_celery_beat', 'ClockedSchedule'),
    ('django_celery_results', 'TaskResult'),
    ('django_celery_results', 'GroupResult'),
]

for app_label, model_name in HIDDEN_ADMIN_MODELS:
    try:
        model = django_apps.get_model(app_label, model_name)
    except LookupError:
        continue
    if model in admin.site._registry:
        admin.site.unregister(model)
