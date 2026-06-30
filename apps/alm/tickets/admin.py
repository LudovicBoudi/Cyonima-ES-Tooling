from django.contrib import admin
from .models import Ticket, TicketLog, TicketAttachment


class TicketLogInline(admin.TabularInline):
    model = TicketLog
    extra = 0
    readonly_fields = ('from_status', 'to_status', 'comment', 'hours_spent', 'user', 'created_at')


class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 0


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('get_formatted_number', 'title', 'ticket_type', 'status', 'assigned_to', 'project')
    list_filter = ('ticket_type', 'status', 'project')
    search_fields = ('title', 'description')
    inlines = [TicketLogInline, TicketAttachmentInline]
