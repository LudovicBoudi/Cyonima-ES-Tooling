from django.urls import path
from . import views

urlpatterns = [
    path('<int:project_id>/tickets/', views.ticket_list, name='ticket_list'),
    path('<int:project_id>/tickets/creer/', views.ticket_create, name='ticket_create'),
    path('<int:project_id>/tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('<int:project_id>/tickets/kanban/', views.ticket_kanban, name='ticket_kanban'),
    path('<int:project_id>/tickets/gantt/', views.ticket_gantt, name='ticket_gantt'),
    path('<int:project_id>/tickets/export/csv/', views.ticket_export_csv, name='ticket_export_csv'),
]
