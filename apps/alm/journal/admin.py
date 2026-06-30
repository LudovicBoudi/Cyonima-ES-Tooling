from django.contrib import admin
from .models import ActivityReport


@admin.register(ActivityReport)
class ActivityReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'report_date')
    list_filter = ('project', 'report_date')
