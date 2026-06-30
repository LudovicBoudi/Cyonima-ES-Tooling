from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.budget_home, name='budget_home'),
    path('dashboard/', include('apps.budget.dashboard.urls')),
    path('dat/', include('apps.budget.dat.urls')),
    path('budgets/', include('apps.budget.budgets.urls')),
    path('taches/', include('apps.budget.todo.urls')),
    path('fournisseurs/', include('apps.budget.providers.urls')),
]
