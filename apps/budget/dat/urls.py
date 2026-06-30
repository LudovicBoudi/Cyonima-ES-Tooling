from django.urls import path
from . import views

urlpatterns = [
    path('', views.dat_list, name='dat_list'),
    path('nouveau/', views.dat_create, name='dat_create'),
    path('<int:pk>/', views.dat_detail, name='dat_detail'),
    path('<int:pk>/modifier/', views.dat_update, name='dat_update'),
    path('<int:pk>/supprimer/', views.dat_delete, name='dat_delete'),
    path('<int:pk>/soumettre/', views.dat_submit, name='dat_submit'),
    path('<int:pk>/valider/', views.dat_validate, name='dat_validate'),
    path('<int:pk>/refuser/', views.dat_reject, name='dat_reject'),
    path('<int:pk>/brouillon/', views.dat_draft, name='dat_draft'),
    path('<int:pk>/dupliquer/', views.dat_duplicate, name='dat_duplicate'),
    path('<int:pk>/csv/', views.dat_export_csv, name='dat_export_csv'),
    path('<int:pk>/xlsx/', views.dat_export_xlsx, name='dat_export_xlsx'),
    path('<int:pk>/pdf/', views.dat_export_pdf, name='dat_export_pdf'),
]
