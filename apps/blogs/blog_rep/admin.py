from django.contrib import admin
from .models import RepSyndicaleArticle


@admin.register(RepSyndicaleArticle)
class RepSyndicaleArticleAdmin(admin.ModelAdmin):
    list_display = ('display_id', 'title', 'created_by', 'created_at')
    search_fields = ('title', 'content')
