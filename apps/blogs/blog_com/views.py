from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from .models import ComArticle, ComArticleAttachment
from apps.notifications.utils import create_notification
from apps.core.sanitizer import sanitize_html


def can_write(user):
    return hasattr(user, 'profile') and user.profile.can_write_blog('communication')


@login_required
def article_list(request):
    articles = ComArticle.objects.all()
    user_can_write = can_write(request.user)
    if not user_can_write:
        articles = articles.filter(Q(status='publie') | Q(created_by=request.user))
    q = request.GET.get('q', '')
    tag = request.GET.get('tag', '')
    if q:
        articles = articles.filter(Q(title__icontains=q) | Q(content__icontains=q))
    if tag:
        articles = articles.filter(tags__icontains=tag)
    paginator = Paginator(articles, 15)
    page = paginator.get_page(request.GET.get('page'))
    all_tags = set()
    for t in ComArticle.objects.filter(status='publie').values_list('tags', flat=True):
        for tag_name in (t or '').split(','):
            name = tag_name.strip()
            if name:
                all_tags.add(name)
    return render(request, 'blogs/article_list.html', {
        'articles': page,
        'blog_title': 'Blog Communication',
        'list_url': 'com_blog_list',
        'create_url': 'com_blog_create',
        'detail_url': 'com_blog_detail',
        'edit_url': 'com_blog_edit',
        'can_write': user_can_write,
        'delete_url': 'com_blog_delete',
        'q': q,
        'current_tag': tag,
        'all_tags': sorted(all_tags),
    })


@login_required
def article_detail(request, article_id):
    article = get_object_or_404(ComArticle, id=article_id)
    if article.status == 'brouillon' and request.user != article.created_by and not (hasattr(request.user, 'profile') and request.user.profile.is_admin()):
        messages.error(request, "Cet article n'est pas publié.")
        return redirect('com_blog_list')
    articles = ComArticle.objects.filter(status='publie')
    return render(request, 'blogs/article_detail.html', {
        'article': article,
        'articles': articles,
        'blog_title': 'Blog Communication',
        'list_url': 'com_blog_list',
        'create_url': 'com_blog_create',
        'detail_url': 'com_blog_detail',
        'edit_url': 'com_blog_edit',
        'can_write': can_write(request.user),
        'content_type': 'blog_com.ComArticle',
    })


@login_required
def article_create(request):
    if not can_write(request.user):
        messages.error(request, "Vous n'avez pas les droits pour écrire dans ce blog.")
        return redirect('com_blog_list')
    if request.method == 'POST':
        article = ComArticle.objects.create(
            title=request.POST['title'],
            content=sanitize_html(request.POST['content']),
            image=request.FILES.get('image'),
            status=request.POST.get('status', 'publie'),
            tags=request.POST.get('tags', ''),
            created_by=request.user,
        )
        attachment = request.FILES.get('attachment')
        if attachment:
            ComArticleAttachment.objects.create(
                article=article,
                file=attachment,
                filename=attachment.name,
            )
        create_notification(
            request.user,
            f"Nouvel article : {article.display_id()}",
            f"Article publié dans le blog Communication : {article.title}",
            link='',
        )
        messages.success(request, f"Article {article.display_id()} créé.")
        return redirect('com_blog_detail', article_id=article.id)
    return render(request, 'blogs/article_form.html', {
        'page': None,
        'blog_title': 'Blog Communication',
        'list_url': 'com_blog_list',
        'create_url': 'com_blog_create',
        'detail_url': 'com_blog_detail',
        'edit_url': 'com_blog_edit',
    })


@login_required
def article_edit(request, article_id):
    article = get_object_or_404(ComArticle, id=article_id)
    if request.user != article.created_by and not (hasattr(request.user, 'profile') and request.user.profile.is_admin()):
        messages.error(request, "Vous ne pouvez pas modifier cet article.")
        return redirect('com_blog_detail', article_id=article.id)
    if request.method == 'POST':
        article.title = request.POST['title']
        article.content = sanitize_html(request.POST['content'])
        article.status = request.POST.get('status', 'publie')
        article.tags = request.POST.get('tags', '')
        if request.FILES.get('image'):
            article.image = request.FILES['image']
        article.save()
        attachment = request.FILES.get('attachment')
        if attachment:
            ComArticleAttachment.objects.create(
                article=article,
                file=attachment,
                filename=attachment.name,
            )
        messages.success(request, f"Article {article.display_id()} modifié.")
        return redirect('com_blog_detail', article_id=article.id)
    return render(request, 'blogs/article_form.html', {
        'page': article,
        'blog_title': 'Blog Communication',
        'list_url': 'com_blog_list',
        'create_url': 'com_blog_create',
        'detail_url': 'com_blog_detail',
        'edit_url': 'com_blog_edit',
    })


@login_required
def article_delete(request, article_id):
    article = get_object_or_404(ComArticle, id=article_id)
    if request.user != article.created_by and not (hasattr(request.user, 'profile') and request.user.profile.is_admin()):
        messages.error(request, "Vous ne pouvez pas supprimer cet article.")
        return redirect('com_blog_detail', article_id=article.id)
    if request.method == 'POST':
        article.delete()
        messages.success(request, "Article supprimé.")
        return redirect('com_blog_list')
    return render(request, 'blogs/article_confirm_delete.html', {
        'article': article,
        'list_url': 'com_blog_list',
    })
