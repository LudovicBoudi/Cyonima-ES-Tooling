from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q


@login_required
def home(request):
    tiles = [
        {'title': 'Gestion budgétaire IT', 'description': 'Budgets, fournisseurs, DAT et tableau de bord', 'icon': 'images/IT-budget-icon.png', 'url': '/budget/'},
        {'title': 'Guichet IT', 'description': "Tickets d'incidents et expressions de besoins informatiques", 'icon': 'images/IT-guichet-icon.png', 'url': '/guichet/'},
        {'title': 'Wiki',                     'description': 'Base de connaissances collaborative',           'icon': 'images/wiki-icon.png',              'url': '/wiki/'},
        {'title': 'CRM',                      'description': 'Gestion de la relation client (contacts, affaires, interactions)', 'icon': 'images/crm-icon.png', 'url': '/crm/'},
        {'title': 'Ressources Humaines',       'description': 'Employés, contrats, congés, départements',                 'icon': 'images/hr-icon.png',              'url': '/rh/'},
        {'title': 'ERP', 'description': 'Devis, factures, avoirs, paiements', 'icon': 'images/erp-icon.png', 'url': '/erp/'},
        {'title': 'GED', 'description': 'Gestion électronique de documents', 'icon': 'images/ged-icon.png', 'url': '/ged/'},
        {'title': 'Ressources Externes', 'description': 'Références réglementaires (RGPD, IGI 1300, IM 900, II 901)', 'icon': 'images/ressources-icon.png', 'url': '/ressources/'},
        {'title': 'Gestion de projet ALM', 'description': 'Projets, exigences, tests, tickets', 'icon': 'images/Project-icon.png', 'url': '/projects/'},
        {'title': 'Blog Sécurité', 'description': 'Actualités et alertes sécurité', 'icon': 'images/Security-blog-icon.png', 'url': '/blog/securite/'},
        {'title': 'Blog Direction', 'description': 'Communications de la direction générale', 'icon': 'images/DG-blog-icon.png', 'url': '/blog/direction/'},
        {'title': 'Blog Communication', 'description': 'Informations et actualités', 'icon': 'images/com-blog-icon.png', 'url': '/blog/communication/'},
        {'title': 'Blog IT', 'description': 'Actualités techniques et IT', 'icon': 'images/IT-blog-icon.png', 'url': '/blog/it/'},
        {'title': 'Blog Rep. Syndicale', 'description': "Actualités de la représentation syndicale", 'icon': 'images/rep-syndicale-blog-icon.png', 'url': '/blog/representation-syndicale/'},
        {'title': 'Zone COMEX', 'description': "Espace d'échange du comité exécutif", 'icon': 'images/COMEX-exchange-zone-icon.png', 'url': '/comex/'},
    ]
    if request.user.is_staff:
        tiles.insert(0, {'title': 'Administration', 'description': 'Gestion des utilisateurs, rôles, configuration, sauvegarde et analytics', 'icon': 'images/Global-App-logo-icon.png', 'url': '/administration/'})

    activities = _recent_activity(request)
    return render(request, 'home.html', {'tiles': tiles, 'activities': activities})


def _search_model(queryset, fields, q, icon, url_prefix, url_field='pk', url_suffix=''):
    results = []
    query = Q()
    for f in fields:
        query |= Q(**{f'{f}__icontains': q})
    for obj in queryset.filter(query)[:5]:
        pk = getattr(obj, url_field)
        url = f'{url_prefix}{pk}{url_suffix}'
        if hasattr(obj, 'display_id'):
            title = f'{obj.display_id()} - {getattr(obj, "title", "")}'
        else:
            title = str(obj)
        desc = ''
        if hasattr(obj, 'description'):
            desc = (obj.description or '')[:200]
        elif hasattr(obj, 'content'):
            desc = (obj.content or '')[:200]
        results.append({'icon': icon, 'title': title, 'description': desc, 'url': url})
    return results


@login_required
def global_search(request):
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        from apps.wiki.models import WikiPage
        results += _search_model(WikiPage.objects, ['title', 'content'], q, '📖', '/wiki/', 'slug')

        from apps.ged.models import Document
        results += _search_model(Document.objects.filter(deleted_at__isnull=True), ['title', 'description'], q, '📁', '/ged/', 'pk')

        from apps.crm.models import Company, Contact
        results += _search_model(Company.objects, ['name'], q, '🏢', '/crm/societes/', 'pk')
        results += _search_model(Contact.objects, ['first_name', 'last_name', 'email'], q, '👤', '/crm/contacts/', 'pk')

        from apps.hr.models import Employee
        results += _search_model(Employee.objects, ['first_name', 'last_name', 'email'], q, '👥', '/rh/employes/', 'pk')

        from apps.budget.dat.models import DAT
        results += _search_model(DAT.objects, ['description'], q, '📋', '/budget/dat/', 'pk')

        from apps.erp.models import Quotation, Invoice, SupplierInvoice
        results += _search_model(Quotation.objects, ['number'], q, '📄', '/erp/devis/', 'pk')
        results += _search_model(Invoice.objects, ['number'], q, '🧾', '/erp/factures/', 'pk')
        results += _search_model(SupplierInvoice.objects, ['internal_number', 'number'], q, '🧾', '/erp/factures-fournisseurs/', 'pk')

    return render(request, 'core/search_results.html', {'q': q, 'results': results})


def _recent_activity(request):
    activities = []
    from django.utils import timezone

    try:
        from apps.wiki.models import WikiPage
        for p in WikiPage.objects.order_by('-updated_at')[:3]:
            activities.append({'icon': '📖', 'text': f'{p.title} — page wiki mise à jour', 'time': p.updated_at, 'url': f'/wiki/{p.slug}/'})
    except Exception:
        pass
    try:
        from apps.ged.models import Document
        for d in Document.objects.filter(deleted_at__isnull=True).order_by('-created_at')[:3]:
            activities.append({'icon': '📁', 'text': f'{d.title} — document ajouté', 'time': d.created_at, 'url': f'/ged/{d.pk}/'})
    except Exception:
        pass
    try:
        from apps.blogs.blog_com.models import ComArticle
        from apps.blogs.blog_it.models import ITArticle
        from apps.blogs.sec_blog.models import SecurityArticle
        from apps.blogs.dg_blog.models import DirectionArticle
        from apps.blogs.blog_rep.models import RepSyndicaleArticle
        articles = []
        for m in [ComArticle, ITArticle, SecurityArticle, DirectionArticle, RepSyndicaleArticle]:
            try:
                articles.extend(m.objects.order_by('-created_at')[:1])
            except Exception:
                pass
        articles.sort(key=lambda a: a.created_at, reverse=True)
        for a in articles[:3]:
            activities.append({'icon': '📝', 'text': f'{a.title} — article publié', 'time': a.created_at, 'url': '#'})
    except Exception:
        pass
    try:
        from apps.alm.tickets.models import Ticket
        for t in Ticket.objects.order_by('-updated_at')[:3]:
            activities.append({'icon': '🎫', 'text': f'{t.get_formatted_number()} {t.title}', 'time': t.updated_at, 'url': f'/projects/{t.project_id}/tickets/{t.id}/'})
    except Exception:
        pass

    activities.sort(key=lambda a: a['time'], reverse=True)
    return activities[:10]
