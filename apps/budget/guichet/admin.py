from django.contrib import admin
from .models import GuichetTicket, GuichetLog


class GuichetLogInline(admin.TabularInline):
    model = GuichetLog
    extra = 0
    readonly_fields = ('user', 'from_status', 'to_status', 'comment', 'created_at')


@admin.register(GuichetTicket)
class GuichetTicketAdmin(admin.ModelAdmin):
    list_display = ('get_formatted_number', 'title', 'ticket_type', 'status', 'assigned_to')
    list_filter = ('ticket_type', 'status')
    search_fields = ('title', 'description')
    inlines = [GuichetLogInline]
