from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('preferences/', views.notification_preferences, name='notification_preferences'),
]
