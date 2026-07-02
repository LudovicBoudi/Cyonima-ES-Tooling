from django.urls import path
from . import views

urlpatterns = [
    path('<int:project_id>/repos/', views.repo_list, name='repo_list'),
    path('<int:project_id>/repos/creer/', views.repo_create, name='repo_create'),
    path('<int:project_id>/repos/<int:repo_id>/', views.repo_detail, name='repo_detail'),
    path('<int:project_id>/repos/<int:repo_id>/supprimer/', views.repo_delete, name='repo_delete'),
    path('<int:project_id>/repos/<int:repo_id>/commits/', views.repo_commits, name='repo_commits'),
    path('<int:project_id>/repos/<int:repo_id>/commits/<str:commit_hash>/', views.repo_commit_detail, name='repo_commit_detail'),
    path('<int:project_id>/repos/<int:repo_id>/arborescence/', views.repo_tree, name='repo_tree'),
    path('<int:project_id>/repos/<int:repo_id>/fichier/', views.repo_file, name='repo_file'),
    path('<int:project_id>/repos/<int:repo_id>/contributeurs/', views.repo_contributors, name='repo_contributors'),
    path('<int:project_id>/repos/<int:repo_id>/pull/', views.repo_pull, name='repo_pull'),
    path('<int:project_id>/repos/<int:repo_id>/fetch/', views.repo_fetch, name='repo_fetch'),
]
