from django.urls import path
from . import views

urlpatterns = [
    path('<int:project_id>/tickets/', views.ticket_list, name='ticket_list'),
    path('<int:project_id>/tickets/creer/', views.ticket_create, name='ticket_create'),
    path('<int:project_id>/tickets/<int:ticket_id>/modifier/', views.ticket_edit, name='ticket_edit'),
    path('<int:project_id>/tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('<int:project_id>/tickets/kanban/', views.ticket_kanban, name='ticket_kanban'),
    path('<int:project_id>/tickets/kanban/update/', views.ticket_kanban_update, name='ticket_kanban_update'),
    path('<int:project_id>/tickets/gantt/', views.ticket_gantt, name='ticket_gantt'),
    path('<int:project_id>/tickets/export/csv/', views.ticket_export_csv, name='ticket_export_csv'),
    path('<int:project_id>/tickets/importer/', views.ticket_import_csv, name='ticket_import_csv'),
    path('<int:project_id>/sprints/', views.sprint_list, name='sprint_list'),
    path('<int:project_id>/sprints/creer/', views.sprint_create, name='sprint_create'),
    path('<int:project_id>/sprints/<int:sprint_id>/', views.sprint_detail, name='sprint_detail'),
    path('<int:project_id>/sprints/<int:sprint_id>/ajouter-tickets/', views.sprint_add_tickets, name='sprint_add_tickets'),
    path('<int:project_id>/releases/', views.release_list, name='release_list'),
    path('<int:project_id>/releases/creer/', views.release_create, name='release_create'),
    path('<int:project_id>/releases/<int:release_id>/', views.release_detail, name='release_detail'),
    path('<int:project_id>/releases/<int:release_id>/ajouter-tickets/', views.release_add_tickets, name='release_add_tickets'),
]
