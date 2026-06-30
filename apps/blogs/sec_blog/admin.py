from django.contrib import admin
from .models import SecurityArticle


@admin.register(SecurityArticle)
class SecurityArticleAdmin(admin.ModelAdmin):
    list_display = ('display_id', 'title', 'created_by', 'created_at')
    search_fields = ('title', 'content')
