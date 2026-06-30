from django.contrib import admin
from .models import Provider


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'sales_contact', 'phone', 'email')
    search_fields = ('company_name', 'sales_contact', 'email')
