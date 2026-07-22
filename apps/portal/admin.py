from django.contrib import admin
from .models import PortalUser


@admin.register(PortalUser)
class PortalUserAdmin(admin.ModelAdmin):
    list_display = ('contact', 'user', 'is_active', 'invited_at', 'activated_at')
    list_filter = ('is_active',)
    search_fields = ('contact__first_name', 'contact__last_name', 'user__username')
