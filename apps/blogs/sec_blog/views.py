from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from .models import SecurityArticle, SecurityArticleAttachment
from apps.notifications.utils import create_notification


def can_write(user):
    return hasattr(user, 'profile') and user.profile.can_write_blog('security')


@login_required
def article_list(request):
    articles = SecurityArticle.objects.all()
    q = request.GET.get('q', '')
    if q:
        articles = articles.filter(Q(title__icontains=q) | Q(content__icontains=q))
    paginator = Paginator(articles, 15)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'blogs/article_list.html', {
        'articles': page,
        'blog_title': 'Blog Sécurité',
        'list_url': 'sec_blog_list',
        'create_url': 'sec_blog_create',
        'detail_url': 'sec_blog_detail',
        'edit_url': 'sec_blog_edit',
        'can_write': can_write(request.user),
        'delete_url': 'sec_blog_delete',
        'q': q,
    })


@login_required
def article_detail(request, article_id):
    article = get_object_or_404(SecurityArticle, id=article_id)
    articles = SecurityArticle.objects.all()
    return render(request, 'blogs/article_detail.html', {
        'article': article,
        'articles': articles,
        'blog_title': 'Blog Sécurité',
        'list_url': 'sec_blog_list',
        'create_url': 'sec_blog_create',
        'detail_url': 'sec_blog_detail',
        'edit_url': 'sec_blog_edit',
        'can_write': can_write(request.user),
    })


@login_required
def article_create(request):
    if not can_write(request.user):
        messages.error(request, "Vous n'avez pas les droits pour écrire dans ce blog.")
        return redirect('sec_blog_list')
    if request.method == 'POST':
        article = SecurityArticle.objects.create(
            title=request.POST['title'],
            content=request.POST['content'],
            image=request.FILES.get('image'),
            created_by=request.user,
        )
        attachment = request.FILES.get('attachment')
        if attachment:
            SecurityArticleAttachment.objects.create(
                article=article,
                file=attachment,
                filename=attachment.name,
            )
        create_notification(
            request.user,
            f"Nouvel article : {article.display_id()}",
            f"Article publié dans le blog Sécurité : {article.title}",
            link='',
        )
        messages.success(request, f"Article {article.display_id()} créé.")
        return redirect('sec_blog_detail', article_id=article.id)
    return render(request, 'blogs/article_form.html', {
        'page': None,
        'blog_title': 'Blog Sécurité',
        'list_url': 'sec_blog_list',
        'create_url': 'sec_blog_create',
        'detail_url': 'sec_blog_detail',
        'edit_url': 'sec_blog_edit',
    })


@login_required
def article_edit(request, article_id):
    article = get_object_or_404(SecurityArticle, id=article_id)
    if request.user != article.created_by and not (hasattr(request.user, 'profile') and request.user.profile.is_admin()):
        messages.error(request, "Vous ne pouvez pas modifier cet article.")
        return redirect('sec_blog_detail', article_id=article.id)
    if request.method == 'POST':
        article.title = request.POST['title']
        article.content = request.POST['content']
        if request.FILES.get('image'):
            article.image = request.FILES['image']
        article.save()
        attachment = request.FILES.get('attachment')
        if attachment:
            SecurityArticleAttachment.objects.create(
                article=article,
                file=attachment,
                filename=attachment.name,
            )
        messages.success(request, f"Article {article.display_id()} modifié.")
        return redirect('sec_blog_detail', article_id=article.id)
    return render(request, 'blogs/article_form.html', {
        'page': article,
        'blog_title': 'Blog Sécurité',
        'list_url': 'sec_blog_list',
        'create_url': 'sec_blog_create',
        'detail_url': 'sec_blog_detail',
        'edit_url': 'sec_blog_edit',
    })


@login_required
def article_delete(request, article_id):
    article = get_object_or_404(SecurityArticle, id=article_id)
    if request.user != article.created_by and not (hasattr(request.user, 'profile') and request.user.profile.is_admin()):
        messages.error(request, "Vous ne pouvez pas supprimer cet article.")
        return redirect('sec_blog_detail', article_id=article.id)
    if request.method == 'POST':
        article.delete()
        messages.success(request, "Article supprimé.")
        return redirect('sec_blog_list')
    return render(request, 'blogs/article_confirm_delete.html', {
        'article': article,
        'list_url': 'sec_blog_list',
    })
