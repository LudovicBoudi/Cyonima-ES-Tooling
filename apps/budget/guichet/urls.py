from django.urls import path
from . import views

urlpatterns = [
    path('', views.ticket_list, name='guichet_list'),
    path('creer/', views.ticket_create, name='guichet_create'),
    path('<int:pk>/', views.ticket_detail, name='guichet_detail'),
]
