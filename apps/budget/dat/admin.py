from django.contrib import admin
from .models import DAT, DATLine


class DATLineInline(admin.TabularInline):
    model = DATLine
    extra = 1


@admin.register(DAT)
class DATAdmin(admin.ModelAdmin):
    list_display = ('display_id', 'provider', 'status', 'total_cost', 'created_date')
    list_filter = ('status', 'year')
    search_fields = ('description', 'provider__company_name')
    inlines = [DATLineInline]
