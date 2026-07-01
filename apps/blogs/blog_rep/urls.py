from django.urls import path
from . import views

urlpatterns = [
    path('', views.article_list, name='rep_syndicale_blog_list'),
    path('<int:article_id>/', views.article_detail, name='rep_syndicale_blog_detail'),
    path('creer/', views.article_create, name='rep_syndicale_blog_create'),
    path('<int:article_id>/modifier/', views.article_edit, name='rep_syndicale_blog_edit'),
    path('<int:article_id>/supprimer/', views.article_delete, name='rep_syndicale_blog_delete'),
]
