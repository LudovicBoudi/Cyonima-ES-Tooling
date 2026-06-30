from django.contrib import admin
from .models import TestScenario, TestStep, TestCampaign, CampaignTest, TestAttachment


class TestStepInline(admin.TabularInline):
    model = TestStep
    extra = 3
    max_num = 10


@admin.register(TestScenario)
class TestScenarioAdmin(admin.ModelAdmin):
    list_display = ('get_formatted_number', 'name', 'project')
    search_fields = ('name',)
    inlines = [TestStepInline]


@admin.register(TestCampaign)
class TestCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'created_at')
