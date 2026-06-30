from django.urls import path
from . import views

urlpatterns = [
    path('<int:project_id>/journal/', views.journal_list, name='journal_list'),
    path('<int:project_id>/journal/creer/', views.journal_create, name='journal_create'),
]
