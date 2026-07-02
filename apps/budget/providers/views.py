from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.shortcuts import render, redirect, get_object_or_404
from .models import Provider


@login_required
def provider_list(request):
    providers = Provider.objects.all()
    return render(request, 'budget/provider_list.html', {'providers': providers})


@login_required
def provider_create(request):
    if request.method == 'POST':
        name = request.POST.get('company_name', '').strip()
        if not name:
            messages.error(request, "Le nom de l'entreprise est requis.")
            return render(request, 'budget/provider_form.html', {'title': 'Nouveau fournisseur'})
        Provider.objects.create(
            company_name=name,
            sales_contact=request.POST.get('sales_contact', ''),
            phone=request.POST.get('phone', ''),
            email=request.POST.get('email', ''),
            description=request.POST.get('description', ''),
        )
        messages.success(request, 'Fournisseur créé.')
        return redirect('provider_list')
    return render(request, 'budget/provider_form.html', {'title': 'Nouveau fournisseur'})


@login_required
def provider_edit(request, pk):
    provider = get_object_or_404(Provider, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('company_name', '').strip()
        if not name:
            messages.error(request, "Le nom de l'entreprise est requis.")
            return render(request, 'budget/provider_form.html', {'provider': provider, 'title': 'Modifier fournisseur'})
        provider.company_name = name
        provider.sales_contact = request.POST.get('sales_contact', '')
        provider.phone = request.POST.get('phone', '')
        provider.email = request.POST.get('email', '')
        provider.description = request.POST.get('description', '')
        provider.save()
        messages.success(request, 'Fournisseur modifié.')
        return redirect('provider_list')
    return render(request, 'budget/provider_form.html', {'provider': provider, 'title': 'Modifier fournisseur'})


@login_required
def provider_delete(request, pk):
    provider = get_object_or_404(Provider, pk=pk)
    if request.method == 'POST':
        try:
            provider.delete()
            messages.success(request, 'Fournisseur supprimé.')
        except ProtectedError:
            messages.error(request, 'Impossible de supprimer ce fournisseur car il est lié à des DAT existantes.')
        return redirect('provider_list')
    return render(request, 'budget/provider_confirm_delete.html', {'provider': provider})
