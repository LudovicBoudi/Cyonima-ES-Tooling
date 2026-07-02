from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from apps.blogs import views as blog_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('administration/', include('apps.administration.urls')),
    path('administration/analytiques/', include('apps.analytics.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('projects/', include('apps.alm.projects.urls')),
    path('projects/', include('apps.alm.requirements.urls')),
    path('projects/', include('apps.alm.tests.urls')),
    path('projects/', include('apps.alm.tickets.urls')),
    path('projects/', include('apps.alm.journal.urls')),
    path('projects/', include('apps.alm.reports.urls')),
    path('projects/', include('apps.alm.repositories.urls')),
    path('budget/', include('apps.budget.urls')),
    path('guichet/', include('apps.budget.guichet.urls')),
    path('wiki/', include('apps.wiki.urls')),
    path('crm/', include('apps.crm.urls')),
    path('rh/', include('apps.hr.urls')),
    path('erp/', include('apps.erp.urls')),
    path('ged/', include('apps.ged.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('ressources/', include('apps.ressources.urls')),
    path('blog/', include('apps.blogs.urls')),
    path('blog/securite/', include('apps.blogs.sec_blog.urls')),
    path('blog/direction/', include('apps.blogs.dg_blog.urls')),
    path('blog/communication/', include('apps.blogs.blog_com.urls')),
    path('blog/it/', include('apps.blogs.blog_it.urls')),
    path('blog/representation-syndicale/', include('apps.blogs.blog_rep.urls')),
    path('comex/', include('apps.blogs.comex_forum.urls')),
    path('', include('apps.core.urls')),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
