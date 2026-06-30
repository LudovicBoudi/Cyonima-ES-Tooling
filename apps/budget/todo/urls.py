from django.urls import path
from . import views

urlpatterns = [
    path('', views.todo_kanban, name='todo_kanban'),
    path('ajouter/', views.todo_create, name='todo_create'),
    path('<int:pk>/supprimer/', views.todo_delete, name='todo_delete'),
    path('<int:pk>/statut/', views.todo_update_status, name='todo_update_status'),
]
