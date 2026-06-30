from django.contrib import admin
from .models import ITArticle


@admin.register(ITArticle)
class ITArticleAdmin(admin.ModelAdmin):
    list_display = ('display_id', 'title', 'created_by', 'created_at')
    search_fields = ('title', 'content')
