from django.urls import path
from . import views

urlpatterns = [
    path('<int:project_id>/tests/', views.test_list, name='test_list'),
    path('<int:project_id>/tests/creer/', views.test_create, name='test_create'),
    path('<int:project_id>/tests/<int:test_id>/modifier/', views.test_edit, name='test_edit'),
    path('<int:project_id>/tests/<int:test_id>/supprimer/', views.test_delete, name='test_delete'),
    path('<int:project_id>/tests/<int:test_id>/executer/', views.test_execute, name='test_execute'),
    path('<int:project_id>/tests/csv/', views.test_export_csv, name='test_export_csv'),
    path('<int:project_id>/campagnes/', views.campaign_list, name='campaign_list'),
    path('<int:project_id>/campagnes/creer/', views.campaign_create, name='campaign_create'),
    path('<int:project_id>/campagnes/<int:campaign_id>/', views.campaign_detail, name='campaign_detail'),
    path('<int:project_id>/campagnes/<int:campaign_id>/update-status/', views.campaign_update_status, name='campaign_update_status'),
    path('<int:project_id>/campagnes/<int:campaign_id>/ajouter-tests/', views.campaign_add_tests, name='campaign_add_tests'),
    path('<int:project_id>/campagnes/<int:campaign_id>/supprimer/', views.campaign_delete, name='campaign_delete'),
    path('<int:project_id>/campagnes/<int:campaign_id>/rapport/', views.campaign_report, name='campaign_report'),
    path('<int:project_id>/campagnes/<int:campaign_id>/csv/', views.campaign_export_csv, name='campaign_export_csv'),
]
