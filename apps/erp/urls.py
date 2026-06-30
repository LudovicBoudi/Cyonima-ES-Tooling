from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='erp_dashboard'),
    path('devis/', views.quotation_list, name='erp_quotation_list'),
    path('devis/creer/', views.quotation_create, name='erp_quotation_create'),
    path('devis/<int:pk>/', views.quotation_detail, name='erp_quotation_detail'),
    path('devis/<int:pk>/modifier/', views.quotation_edit, name='erp_quotation_edit'),
    path('devis/<int:pk>/supprimer/', views.quotation_delete, name='erp_quotation_delete'),
    path('devis/<int:pk>/convertir/', views.quotation_convert, name='erp_quotation_convert'),
    path('factures/', views.invoice_list, name='erp_invoice_list'),
    path('factures/creer/', views.invoice_create, name='erp_invoice_create'),
    path('factures/<int:pk>/', views.invoice_detail, name='erp_invoice_detail'),
    path('factures/<int:pk>/modifier/', views.invoice_edit, name='erp_invoice_edit'),
    path('factures/<int:pk>/supprimer/', views.invoice_delete, name='erp_invoice_delete'),
    path('avoirs/', views.creditnote_list, name='erp_creditnote_list'),
    path('avoirs/creer/', views.creditnote_create, name='erp_creditnote_create'),
    path('avoirs/<int:pk>/supprimer/', views.creditnote_delete, name='erp_creditnote_delete'),
    path('factures-fournisseurs/', views.supplier_invoice_list, name='erp_supplier_invoice_list'),
    path('factures-fournisseurs/creer/', views.supplier_invoice_create, name='erp_supplier_invoice_create'),
    path('factures-fournisseurs/<int:pk>/modifier/', views.supplier_invoice_edit, name='erp_supplier_invoice_edit'),
    path('factures-fournisseurs/<int:pk>/supprimer/', views.supplier_invoice_delete, name='erp_supplier_invoice_delete'),
    path('paiements/creer/', views.payment_create, name='erp_payment_create'),
]
