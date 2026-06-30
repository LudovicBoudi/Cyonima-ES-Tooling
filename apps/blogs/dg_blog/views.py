from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import DirectionArticle


def can_write(user):
    return hasattr(user, 'profile') and user.profile.can_write_blog('direction')


@login_required
def article_list(request):
    articles = DirectionArticle.objects.all()
    return render(request, 'blogs/article_list.html', {
        'articles': articles,
        'blog_title': 'Blog Direction Générale',
        'create_url': 'dg_blog_create',
        'detail_url': 'dg_blog_detail',
        'can_write': can_write(request.user),
        'delete_url': 'dg_blog_delete',
    })


@login_required
def article_detail(request, article_id):
    article = get_object_or_404(DirectionArticle, id=article_id)
    return render(request, 'blogs/article_detail.html', {
        'article': article,
        'blog_title': 'Blog Direction Générale',
        'list_url': 'dg_blog_list',
    })


@login_required
def article_create(request):
    if not can_write(request.user):
        messages.error(request, "Vous n'avez pas les droits pour écrire dans ce blog.")
        return redirect('dg_blog_list')
    if request.method == 'POST':
        article = DirectionArticle.objects.create(
            title=request.POST['title'],
            content=request.POST['content'],
            created_by=request.user,
        )
        messages.success(request, f"Article {article.display_id()} créé.")
        return redirect('dg_blog_detail', article_id=article.id)
    return render(request, 'blogs/article_form.html', {
        'blog_title': 'Blog Direction Générale',
        'list_url': 'dg_blog_list',
        'create_url': 'dg_blog_create',
    })


@login_required
def article_delete(request, article_id):
    article = get_object_or_404(DirectionArticle, id=article_id)
    if request.user != article.created_by and not (hasattr(request.user, 'profile') and request.user.profile.is_admin()):
        messages.error(request, "Vous ne pouvez pas supprimer cet article.")
        return redirect('dg_blog_detail', article_id=article.id)
    if request.method == 'POST':
        article.delete()
        messages.success(request, "Article supprimé.")
        return redirect('dg_blog_list')
    return render(request, 'blogs/article_confirm_delete.html', {
        'article': article,
        'list_url': 'dg_blog_list',
    })
