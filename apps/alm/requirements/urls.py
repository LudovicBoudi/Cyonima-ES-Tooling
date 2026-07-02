from django.urls import path
from . import views

urlpatterns = [
    path('<int:project_id>/exigences/', views.requirement_list, name='requirement_list'),
    path('<int:project_id>/exigences/creer/', views.requirement_create, name='requirement_create'),
    path('<int:project_id>/exigences/<int:requirement_id>/modifier/', views.requirement_edit, name='requirement_edit'),
    path('<int:project_id>/exigences/<int:requirement_id>/supprimer/', views.requirement_delete, name='requirement_delete'),
    path('<int:project_id>/tracabilite/', views.traceability_matrix, name='traceability_matrix'),
    path('<int:project_id>/exigences/csv/', views.requirement_export_csv, name='requirement_export_csv'),
    path('<int:project_id>/exigences/importer/', views.requirement_import_csv, name='requirement_import_csv'),
    path('<int:project_id>/exigences/dossier/', views.folder_create, name='folder_create'),
    path('<int:project_id>/exigences/<int:requirement_id>/', views.requirement_detail, name='requirement_detail'),
]
