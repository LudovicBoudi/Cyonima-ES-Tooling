from django.contrib import admin
from .models import ComexThread, ComexMessage


class ComexMessageInline(admin.TabularInline):
    model = ComexMessage
    extra = 0
    readonly_fields = ('content', 'created_by', 'created_at')


@admin.register(ComexThread)
class ComexThreadAdmin(admin.ModelAdmin):
    list_display = ('display_id', 'title', 'created_by', 'created_at')
    inlines = [ComexMessageInline]
