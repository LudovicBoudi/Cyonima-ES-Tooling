from django.urls import path
from . import views

urlpatterns = [
    path('', views.page_list, name='wiki_list'),
    path('creer/', views.page_create, name='wiki_create'),
    path('<slug:slug>/', views.page_detail, name='wiki_detail'),
    path('<slug:slug>/modifier/', views.page_edit, name='wiki_edit'),
    path('<slug:slug>/supprimer/', views.page_delete, name='wiki_delete'),
]
