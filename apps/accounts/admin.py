from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil'


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ('username', 'email', 'get_role', 'is_staff', 'is_active')
    list_select_related = ('profile',)

    def get_role(self, instance):
        if hasattr(instance, 'profile'):
            roles = ', '.join(r.label for r in instance.profile.roles.all()) or '-'
            return roles
        return '-'
    get_role.short_description = 'Rôles'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
