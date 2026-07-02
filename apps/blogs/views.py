from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from apps.blogs.blog_com.models import ComArticle
from apps.blogs.blog_it.models import ITArticle
from apps.blogs.sec_blog.models import SecurityArticle
from apps.blogs.dg_blog.models import DirectionArticle
from apps.blogs.blog_rep.models import RepSyndicaleArticle


@login_required
def blog_index(request):
    blogs = [
        {
            'name': 'Blog Sécurité',
            'description': 'Actualités et alertes cybersécurité',
            'icon': 'images/Security-blog-icon.png',
            'url': 'sec_blog_list',
            'articles': SecurityArticle.objects.filter(status='publie')[:3],
            'can_write': hasattr(request.user, 'profile') and request.user.profile.can_write_blog('security'),
        },
        {
            'name': 'Blog Direction Générale',
            'description': 'Communications de la direction',
            'icon': 'images/DG-blog-icon.png',
            'url': 'dg_blog_list',
            'articles': DirectionArticle.objects.filter(status='publie')[:3],
            'can_write': hasattr(request.user, 'profile') and request.user.profile.can_write_blog('direction'),
        },
        {
            'name': 'Blog Communication',
            'description': 'Informations et actualités internes',
            'icon': 'images/com-blog-icon.png',
            'url': 'com_blog_list',
            'articles': ComArticle.objects.filter(status='publie')[:3],
            'can_write': hasattr(request.user, 'profile') and request.user.profile.can_write_blog('communication'),
        },
        {
            'name': 'Blog IT',
            'description': 'Actualités techniques et informatiques',
            'icon': 'images/IT-blog-icon.png',
            'url': 'it_blog_list',
            'articles': ITArticle.objects.filter(status='publie')[:3],
            'can_write': hasattr(request.user, 'profile') and request.user.profile.can_write_blog('it'),
        },
        {
            'name': 'Blog Représentation Syndicale',
            'description': 'Communications des élus syndicaux',
            'icon': 'images/rep-syndicale-blog-icon.png',
            'url': 'rep_syndicale_blog_list',
            'articles': RepSyndicaleArticle.objects.filter(status='publie')[:3],
            'can_write': hasattr(request.user, 'profile') and request.user.profile.can_write_blog('rep_syndicale'),
        },
    ]
    return render(request, 'blogs/blog_index.html', {'blogs': blogs})
