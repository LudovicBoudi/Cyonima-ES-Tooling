from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='hr_dashboard'),
    path('employes/', views.employee_list, name='hr_employee_list'),
    path('employes/creer/', views.employee_create, name='hr_employee_create'),
    path('employes/<int:pk>/', views.employee_detail, name='hr_employee_detail'),
    path('employes/<int:pk>/modifier/', views.employee_edit, name='hr_employee_edit'),
    path('employes/<int:pk>/supprimer/', views.employee_delete, name='hr_employee_delete'),
    path('departements/', views.department_list, name='hr_department_list'),
    path('departements/creer/', views.department_create, name='hr_department_create'),
    path('departements/<int:pk>/modifier/', views.department_edit, name='hr_department_edit'),
    path('departements/<int:pk>/supprimer/', views.department_delete, name='hr_department_delete'),
    path('contrats/', views.contract_list, name='hr_contract_list'),
    path('contrats/creer/', views.contract_create, name='hr_contract_create'),
    path('contrats/<int:pk>/modifier/', views.contract_edit, name='hr_contract_edit'),
    path('contrats/<int:pk>/supprimer/', views.contract_delete, name='hr_contract_delete'),
    path('conges/', views.leave_list, name='hr_leave_list'),
    path('conges/creer/', views.leave_create, name='hr_leave_create'),
    path('conges/<int:pk>/modifier/', views.leave_edit, name='hr_leave_edit'),
    path('conges/<int:pk>/supprimer/', views.leave_delete, name='hr_leave_delete'),
    path('conges/<int:pk>/valider/', views.leave_approve, name='hr_leave_approve'),
    path('conges/<int:pk>/refuser/', views.leave_reject, name='hr_leave_reject'),
]
