from django.contrib import admin
from .models import ComArticle


@admin.register(ComArticle)
class ComArticleAdmin(admin.ModelAdmin):
    list_display = ('display_id', 'title', 'created_by', 'created_at')
    search_fields = ('title', 'content')
