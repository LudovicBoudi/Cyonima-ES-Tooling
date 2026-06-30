from django.contrib import admin
from .models import BudgetYear


@admin.register(BudgetYear)
class BudgetYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'budget_type', 'amount')
    list_filter = ('year', 'budget_type')
