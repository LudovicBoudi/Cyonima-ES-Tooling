from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from .models import RepSyndicaleArticle, RepSyndicaleArticleAttachment
from apps.notifications.utils import create_notification


def can_write(user):
    return hasattr(user, 'profile') and user.profile.can_write_blog('rep_syndicale')


@login_required
def article_list(request):
    articles = RepSyndicaleArticle.objects.all()
    q = request.GET.get('q', '')
    if q:
        articles = articles.filter(Q(title__icontains=q) | Q(content__icontains=q))
    paginator = Paginator(articles, 15)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'blogs/article_list.html', {
        'articles': page,
        'blog_title': 'Blog Représentation Syndicale',
        'list_url': 'rep_syndicale_blog_list',
        'create_url': 'rep_syndicale_blog_create',
        'detail_url': 'rep_syndicale_blog_detail',
        'edit_url': 'rep_syndicale_blog_edit',
        'can_write': can_write(request.user),
        'delete_url': 'rep_syndicale_blog_delete',
        'q': q,
    })


@login_required
def article_detail(request, article_id):
    article = get_object_or_404(RepSyndicaleArticle, id=article_id)
    articles = RepSyndicaleArticle.objects.all()
    return render(request, 'blogs/article_detail.html', {
        'article': article,
        'articles': articles,
        'blog_title': 'Blog Représentation Syndicale',
        'list_url': 'rep_syndicale_blog_list',
        'create_url': 'rep_syndicale_blog_create',
        'detail_url': 'rep_syndicale_blog_detail',
        'edit_url': 'rep_syndicale_blog_edit',
        'can_write': can_write(request.user),
    })


@login_required
def article_create(request):
    if not can_write(request.user):
        messages.error(request, "Vous n'avez pas les droits pour écrire dans ce blog.")
        return redirect('rep_syndicale_blog_list')
    if request.method == 'POST':
        article = RepSyndicaleArticle.objects.create(
            title=request.POST['title'],
            content=request.POST['content'],
            image=request.FILES.get('image'),
            created_by=request.user,
        )
        attachment = request.FILES.get('attachment')
        if attachment:
            RepSyndicaleArticleAttachment.objects.create(
                article=article,
                file=attachment,
                filename=attachment.name,
            )
        create_notification(
            request.user,
            f"Nouvel article : {article.display_id()}",
            f"Article publié dans le blog Représentation Syndicale : {article.title}",
            link='',
        )
        messages.success(request, f"Article {article.display_id()} créé.")
        return redirect('rep_syndicale_blog_detail', article_id=article.id)
    return render(request, 'blogs/article_form.html', {
        'page': None,
        'blog_title': 'Blog Représentation Syndicale',
        'list_url': 'rep_syndicale_blog_list',
        'create_url': 'rep_syndicale_blog_create',
        'detail_url': 'rep_syndicale_blog_detail',
        'edit_url': 'rep_syndicale_blog_edit',
    })


@login_required
def article_edit(request, article_id):
    article = get_object_or_404(RepSyndicaleArticle, id=article_id)
    if request.user != article.created_by and not (hasattr(request.user, 'profile') and request.user.profile.is_admin()):
        messages.error(request, "Vous ne pouvez pas modifier cet article.")
        return redirect('rep_syndicale_blog_detail', article_id=article.id)
    if request.method == 'POST':
        article.title = request.POST['title']
        article.content = request.POST['content']
        if request.FILES.get('image'):
            article.image = request.FILES['image']
        article.save()
        attachment = request.FILES.get('attachment')
        if attachment:
            RepSyndicaleArticleAttachment.objects.create(
                article=article,
                file=attachment,
                filename=attachment.name,
            )
        messages.success(request, f"Article {article.display_id()} modifié.")
        return redirect('rep_syndicale_blog_detail', article_id=article.id)
    return render(request, 'blogs/article_form.html', {
        'page': article,
        'blog_title': 'Blog Représentation Syndicale',
        'list_url': 'rep_syndicale_blog_list',
        'create_url': 'rep_syndicale_blog_create',
        'detail_url': 'rep_syndicale_blog_detail',
        'edit_url': 'rep_syndicale_blog_edit',
    })


@login_required
def article_delete(request, article_id):
    article = get_object_or_404(RepSyndicaleArticle, id=article_id)
    if request.user != article.created_by and not (hasattr(request.user, 'profile') and request.user.profile.is_admin()):
        messages.error(request, "Vous ne pouvez pas supprimer cet article.")
        return redirect('rep_syndicale_blog_detail', article_id=article.id)
    if request.method == 'POST':
        article.delete()
        messages.success(request, "Article supprimé.")
        return redirect('rep_syndicale_blog_list')
    return render(request, 'blogs/article_confirm_delete.html', {
        'article': article,
        'list_url': 'rep_syndicale_blog_list',
    })
