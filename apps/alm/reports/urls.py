from django.urls import path
from . import views

urlpatterns = [
    path('<int:project_id>/rapports/temps/', views.time_report, name='time_report'),
]
