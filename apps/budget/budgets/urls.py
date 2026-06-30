from django.urls import path
from . import views

urlpatterns = [
    path('', views.budget_list, name='budget_list'),
    path('creer/', views.budget_create, name='budget_create'),
    path('<int:pk>/modifier/', views.budget_edit, name='budget_edit'),
    path('<int:pk>/supprimer/', views.budget_delete, name='budget_delete'),
]
