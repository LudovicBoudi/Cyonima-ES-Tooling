from django.urls import path
from . import views

urlpatterns = [
    path('', views.article_list, name='sec_blog_list'),
    path('<int:article_id>/', views.article_detail, name='sec_blog_detail'),
    path('creer/', views.article_create, name='sec_blog_create'),
    path('<int:article_id>/supprimer/', views.article_delete, name='sec_blog_delete'),
]
