from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import WikiPage, WikiPageVersion, WikiAttachment
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


def _render_wiki_links(html):
    def replace_link(m):
        title = m.group(1).strip()
        from django.utils.text import slugify
        slug = slugify(title)
        return f'<a href="/wiki/{slug}/" class="wiki-link">{title}</a>'
    return re.sub(r'\[\[(.+?)\]\]', replace_link, html)


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
    rendered = _render_wiki_links(page.content)
    return render(request, 'wiki/page_detail.html', {
        'page': page,
        'all_pages': WikiPage.objects.all().order_by('title'),
        'toc': _extract_toc(page.content),
        'rendered_content': rendered,
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
        _handle_attachment(request, page)
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
        last_version = page.versions.order_by('-version_number').first()
        vn = (last_version.version_number + 1) if last_version else 1
        WikiPageVersion.objects.create(
            page=page, title=page.title, content=page.content,
            version_number=vn, created_by=request.user,
        )
        page.title = request.POST['title']
        page.content = sanitize_html(request.POST['content'])
        page.updated_by = request.user
        page.save()
        _handle_attachment(request, page)
        messages.success(request, f'Page "{page.title}" modifiée (version {vn + 1}).')
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


@login_required
def page_versions(request, slug):
    page = get_object_or_404(WikiPage, slug=slug)
    versions = page.versions.select_related('created_by').all()
    return render(request, 'wiki/page_versions.html', {
        'page': page, 'versions': versions,
        'all_pages': WikiPage.objects.all().order_by('title'),
    })


@login_required
def version_restore(request, version_id):
    version = get_object_or_404(WikiPageVersion, pk=version_id)
    page = version.page
    last_vn = page.versions.order_by('-version_number').first()
    vn = (last_vn.version_number + 1) if last_vn else 1
    WikiPageVersion.objects.create(
        page=page, title=page.title, content=page.content,
        version_number=vn, created_by=request.user,
    )
    page.title = version.title
    page.content = version.content
    page.updated_by = request.user
    page.save()
    messages.success(request, f'Version {version.version_number} restaurée.')
    return redirect('wiki_detail', slug=page.slug)


def _handle_attachment(request, page):
    f = request.FILES.get('attachment')
    if f:
        WikiAttachment.objects.create(
            page=page, file=f, filename=f.name,
            uploaded_by=request.user,
        )
