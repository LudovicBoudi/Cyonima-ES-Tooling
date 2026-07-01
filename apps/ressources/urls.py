from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='ressources_home'),
    path('rgpd/', views.rgpd, name='ressources_rgpd'),
    path('igi-1300/', views.igi_1300, name='ressources_igi_1300'),
    path('im-900/', views.im_900, name='ressources_im_900'),
    path('ii-901/', views.ii_901, name='ressources_ii_901'),
    path('pci-dss/', views.pci_dss, name='ressources_pci_dss'),
    path('nis/', views.nis, name='ressources_nis'),
    path('ebios-rm/', views.ebios_rm, name='ressources_ebios_rm'),
    path('iec-62443/', views.iec_62443, name='ressources_iec_62443'),
    path('iso-27001/', views.iso_27001, name='ressources_iso_27001'),
    path('iso-27032/', views.iso_27032, name='ressources_iso_27032'),
    path('convention-metallurgie/', views.convention_metallurgie, name='ressources_convention_metallurgie'),
]
