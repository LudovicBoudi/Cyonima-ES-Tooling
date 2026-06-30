from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import WikiPage


@login_required
def page_list(request):
    pages = WikiPage.objects.all()
    return render(request, 'wiki/page_list.html', {'pages': pages})


@login_required
def page_detail(request, slug):
    page = get_object_or_404(WikiPage, slug=slug)
    return render(request, 'wiki/page_detail.html', {'page': page})


@login_required
def page_create(request):
    if request.method == 'POST':
        page = WikiPage.objects.create(
            title=request.POST['title'],
            content=request.POST['content'],
            created_by=request.user,
            updated_by=request.user,
        )
        messages.success(request, f'Page "{page.title}" créée.')
        return redirect('wiki_detail', slug=page.slug)
    return render(request, 'wiki/page_form.html', {'title': 'Nouvelle page', 'page': None})


@login_required
def page_edit(request, slug):
    page = get_object_or_404(WikiPage, slug=slug)
    if request.method == 'POST':
        page.title = request.POST['title']
        page.content = request.POST['content']
        page.updated_by = request.user
        page.save()
        messages.success(request, f'Page "{page.title}" modifiée.')
        return redirect('wiki_detail', slug=page.slug)
    return render(request, 'wiki/page_form.html', {'page': page, 'title': 'Modifier la page'})


@login_required
def page_delete(request, slug):
    page = get_object_or_404(WikiPage, slug=slug)
    if request.method == 'POST':
        title = page.title
        page.delete()
        messages.success(request, f'Page "{title}" supprimée.')
        return redirect('wiki_list')
    return render(request, 'wiki/page_confirm_delete.html', {'page': page})
