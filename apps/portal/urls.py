from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('connexion/', views.portal_login, name='login'),
    path('deconnexion/', views.portal_logout, name='logout'),
    path('activation/<uuid:token>/', views.portal_activate, name='activate'),
    path('', views.dashboard, name='dashboard'),
    path('devis/', views.quotation_list, name='quotation_list'),
    path('devis/<int:pk>/', views.quotation_detail, name='quotation_detail'),
    path('devis/<int:pk>/pdf/', views.quotation_pdf, name='quotation_pdf'),
    path('factures/', views.invoice_list, name='invoice_list'),
    path('factures/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('factures/<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    path('avoirs/', views.creditnote_list, name='creditnote_list'),
    path('avoirs/<int:pk>/', views.creditnote_detail, name='creditnote_detail'),
    path('avoirs/<int:pk>/pdf/', views.creditnote_pdf, name='creditnote_pdf'),
    path('mon-compte/changer-mot-de-passe/', views.portal_password_change, name='password_change'),
    path('mon-compte/', views.portal_account, name='account'),
]
