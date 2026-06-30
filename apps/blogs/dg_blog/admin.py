from django.contrib import admin
from .models import DirectionArticle


@admin.register(DirectionArticle)
class DirectionArticleAdmin(admin.ModelAdmin):
    list_display = ('display_id', 'title', 'created_by', 'created_at')
    search_fields = ('title', 'content')
