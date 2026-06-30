from django.urls import path
from . import views

urlpatterns = [
    path('<int:project_id>/exigences/', views.requirement_list, name='requirement_list'),
    path('<int:project_id>/exigences/creer/', views.requirement_create, name='requirement_create'),
    path('<int:project_id>/exigences/<int:requirement_id>/modifier/', views.requirement_edit, name='requirement_edit'),
    path('<int:project_id>/exigences/<int:requirement_id>/supprimer/', views.requirement_delete, name='requirement_delete'),
    path('<int:project_id>/traçabilité/', views.traceability_matrix, name='traceability_matrix'),
]
