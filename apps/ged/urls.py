from django.urls import path
from . import views

urlpatterns = [
    path('', views.document_list, name='ged_document_list'),
    path('<int:pk>/', views.document_detail, name='ged_document_detail'),
    path('<int:pk>/telecharger/', views.document_download, name='ged_document_download'),
    path('ajouter/', views.document_create, name='ged_document_create'),
    path('<int:pk>/modifier/', views.document_edit, name='ged_document_edit'),
    path('<int:pk>/supprimer/', views.document_delete, name='ged_document_delete'),
]
