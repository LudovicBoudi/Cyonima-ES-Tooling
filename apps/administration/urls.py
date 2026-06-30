from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='admin_dashboard'),
    path('utilisateurs/', views.user_list, name='admin_user_list'),
    path('utilisateurs/creer/', views.user_create, name='admin_user_create'),
    path('utilisateurs/<int:user_id>/modifier/', views.user_edit, name='admin_user_edit'),
    path('utilisateurs/<int:user_id>/supprimer/', views.user_delete, name='admin_user_delete'),
    path('configuration/', views.site_config_view, name='admin_site_config'),
    path('fournisseurs/', views.provider_list, name='admin_provider_list'),
    path('fournisseurs/creer/', views.provider_create, name='admin_provider_create'),
    path('fournisseurs/<int:pk>/modifier/', views.provider_edit, name='admin_provider_edit'),
    path('fournisseurs/<int:pk>/supprimer/', views.provider_delete, name='admin_provider_delete'),
    path('budgets/', views.budget_list, name='admin_budget_list'),
    path('budgets/creer/', views.budget_create, name='admin_budget_create'),
    path('budgets/<int:pk>/modifier/', views.budget_edit, name='admin_budget_edit'),
    path('budgets/<int:pk>/supprimer/', views.budget_delete, name='admin_budget_delete'),
    path('sauvegarde/', views.backup, name='admin_backup'),
]
