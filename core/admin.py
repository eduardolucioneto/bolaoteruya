from django.contrib import admin

from core.models import PoolConfiguration


@admin.register(PoolConfiguration)
class PoolConfigurationAdmin(admin.ModelAdmin):
    list_display = ("name", "year", "active", "allow_self_signup", "signup_whatsapp_number", "updated_at")
