from django.contrib import admin
from .models import Requirement, RequirementAttachment


class RequirementAttachmentInline(admin.TabularInline):
    model = RequirementAttachment
    extra = 0


@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ('get_formatted_number', 'name', 'project', 'category', 'created_at')
    list_filter = ('category', 'project')
    search_fields = ('name', 'description')
    inlines = [RequirementAttachmentInline]
