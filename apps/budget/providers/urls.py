from django.urls import path
from . import views

urlpatterns = [
    path('', views.provider_list, name='provider_list'),
    path('creer/', views.provider_create, name='provider_create'),
    path('<int:pk>/modifier/', views.provider_edit, name='provider_edit'),
    path('<int:pk>/supprimer/', views.provider_delete, name='provider_delete'),
]
