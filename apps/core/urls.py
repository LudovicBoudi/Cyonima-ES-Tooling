from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('recherche/', views.global_search, name='global_search'),
]
