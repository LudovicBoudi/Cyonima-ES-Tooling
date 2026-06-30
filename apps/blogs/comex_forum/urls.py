from django.urls import path
from . import views

urlpatterns = [
    path('', views.thread_list, name='comex_thread_list'),
    path('creer/', views.thread_create, name='comex_thread_create'),
    path('<int:thread_id>/', views.thread_detail, name='comex_thread_detail'),
]
