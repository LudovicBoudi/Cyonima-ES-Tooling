from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('dashboard/', views.alm_dashboard, name='alm_dashboard'),
    path('creer/', views.project_create, name='project_create'),
    path('<int:project_id>/', views.project_detail, name='project_detail'),
    path('<int:project_id>/modifier/', views.project_edit, name='project_edit'),
    path('<int:project_id>/membres/', views.member_list, name='member_list'),
    path('<int:project_id>/membres/ajouter/', views.member_add, name='member_add'),
    path('<int:project_id>/membres/<int:member_id>/retirer/', views.member_remove, name='member_remove'),
]
