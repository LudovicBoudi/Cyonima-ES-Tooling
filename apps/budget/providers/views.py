from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Provider


@login_required
def provider_list(request):
    providers = Provider.objects.all()
    return render(request, 'budget/provider_list.html', {'providers': providers})


@login_required
def provider_create(request):
    if request.method == 'POST':
        Provider.objects.create(
            company_name=request.POST['company_name'],
            sales_contact=request.POST['sales_contact'],
            phone=request.POST['phone'],
            email=request.POST['email'],
            description=request.POST.get('description', ''),
        )
        messages.success(request, 'Fournisseur créé.')
        return redirect('provider_list')
    return render(request, 'budget/provider_form.html', {'title': 'Nouveau fournisseur'})


@login_required
def provider_edit(request, pk):
    provider = get_object_or_404(Provider, pk=pk)
    if request.method == 'POST':
        provider.company_name = request.POST['company_name']
        provider.sales_contact = request.POST['sales_contact']
        provider.phone = request.POST['phone']
        provider.email = request.POST['email']
        provider.description = request.POST.get('description', '')
        provider.save()
        messages.success(request, 'Fournisseur modifié.')
        return redirect('provider_list')
    return render(request, 'budget/provider_form.html', {'provider': provider, 'title': 'Modifier fournisseur'})


@login_required
def provider_delete(request, pk):
    provider = get_object_or_404(Provider, pk=pk)
    if request.method == 'POST':
        provider.delete()
        messages.success(request, 'Fournisseur supprimé.')
        return redirect('provider_list')
    return render(request, 'budget/provider_confirm_delete.html', {'provider': provider})
