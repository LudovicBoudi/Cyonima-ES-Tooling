from django.contrib import admin
from .models import TodoItem


@admin.register(TodoItem)
class TodoItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'deadline', 'order')
    list_filter = ('status',)
