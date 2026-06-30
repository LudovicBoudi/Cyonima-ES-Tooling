from django.urls import path
from . import views

urlpatterns = [
    path('', views.article_list, name='com_blog_list'),
    path('<int:article_id>/', views.article_detail, name='com_blog_detail'),
    path('creer/', views.article_create, name='com_blog_create'),
    path('<int:article_id>/modifier/', views.article_edit, name='com_blog_edit'),
    path('<int:article_id>/supprimer/', views.article_delete, name='com_blog_delete'),
]
