from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='crm_dashboard'),
    path('societes/', views.company_list, name='crm_company_list'),
    path('societes/creer/', views.company_create, name='crm_company_create'),
    path('societes/<int:pk>/', views.company_detail, name='crm_company_detail'),
    path('societes/<int:pk>/modifier/', views.company_edit, name='crm_company_edit'),
    path('societes/<int:pk>/supprimer/', views.company_delete, name='crm_company_delete'),
    path('contacts/', views.contact_list, name='crm_contact_list'),
    path('contacts/creer/', views.contact_create, name='crm_contact_create'),
    path('contacts/<int:pk>/modifier/', views.contact_edit, name='crm_contact_edit'),
    path('contacts/<int:pk>/supprimer/', views.contact_delete, name='crm_contact_delete'),
    path('affaires/', views.deal_list, name='crm_deal_list'),
    path('affaires/creer/', views.deal_create, name='crm_deal_create'),
    path('affaires/<int:pk>/modifier/', views.deal_edit, name='crm_deal_edit'),
    path('affaires/<int:pk>/supprimer/', views.deal_delete, name='crm_deal_delete'),
    path('interactions/', views.interaction_list, name='crm_interaction_list'),
    path('interactions/creer/', views.interaction_create, name='crm_interaction_create'),
    path('interactions/<int:pk>/modifier/', views.interaction_edit, name='crm_interaction_edit'),
    path('interactions/<int:pk>/supprimer/', views.interaction_delete, name='crm_interaction_delete'),
    path('taches/', views.task_list, name='crm_task_list'),
    path('taches/creer/', views.task_create, name='crm_task_create'),
    path('taches/<int:pk>/modifier/', views.task_edit, name='crm_task_edit'),
    path('taches/<int:pk>/supprimer/', views.task_delete, name='crm_task_delete'),
    path('taches/<int:pk>/basculer/', views.task_toggle, name='crm_task_toggle'),
]
