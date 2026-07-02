from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import WikiPage
from apps.core.sanitizer import sanitize_html
import re


def _extract_toc(html):
    headings = re.findall(r'<h([2-3])[^>]*>(.+?)</h\1>', html, re.DOTALL)
    toc = []
    for level, text in headings:
        clean = re.sub(r'<[^>]+>', '', text).strip()
        anchor = re.sub(r'[^a-z0-9]+', '-', clean.lower()).strip('-')
        toc.append({'id': anchor, 'title': clean, 'level': int(level)})
    return toc


@login_required
def page_list(request):
    q = request.GET.get('q', '')
    pages = WikiPage.objects.all()
    if q:
        pages = pages.filter(Q(title__icontains=q) | Q(content__icontains=q))
    return render(request, 'wiki/page_list.html', {
        'pages': pages, 'q': q,
        'all_pages': WikiPage.objects.all().order_by('title'),
    })


@login_required
def page_detail(request, slug):
    page = get_object_or_404(WikiPage, slug=slug)
    return render(request, 'wiki/page_detail.html', {
        'page': page,
        'all_pages': WikiPage.objects.all().order_by('title'),
        'toc': _extract_toc(page.content),
    })


@login_required
def page_create(request):
    if request.method == 'POST':
        page = WikiPage.objects.create(
            title=request.POST['title'],
            content=sanitize_html(request.POST['content']),
            created_by=request.user,
            updated_by=request.user,
        )
        messages.success(request, f'Page "{page.title}" créée.')
        return redirect('wiki_detail', slug=page.slug)
    return render(request, 'wiki/page_form.html', {
        'title': 'Nouvelle page', 'page': None,
        'all_pages': WikiPage.objects.all().order_by('title'),
    })


@login_required
def page_edit(request, slug):
    page = get_object_or_404(WikiPage, slug=slug)
    if request.method == 'POST':
        page.title = request.POST['title']
        page.content = sanitize_html(request.POST['content'])
        page.updated_by = request.user
        page.save()
        messages.success(request, f'Page "{page.title}" modifiée.')
        return redirect('wiki_detail', slug=page.slug)
    return render(request, 'wiki/page_form.html', {
        'page': page, 'title': 'Modifier la page',
        'all_pages': WikiPage.objects.all().order_by('title'),
    })


@login_required
def page_delete(request, slug):
    page = get_object_or_404(WikiPage, slug=slug)
    if request.method == 'POST':
        title = page.title
        page.delete()
        messages.success(request, f'Page "{title}" supprimée.')
        return redirect('wiki_list')
    return render(request, 'wiki/page_confirm_delete.html', {
        'page': page,
        'all_pages': WikiPage.objects.all().order_by('title'),
    })
