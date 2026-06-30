from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def home(request):
    tiles = [
        {'title': 'Gestion budgétaire IT', 'description': 'Budgets, fournisseurs, DAT et tableau de bord', 'icon': 'images/IT-budget-icon.png', 'url': '/budget/'},
        {'title': 'Guichet IT', 'description': "Tickets d'incidents et expressions de besoins informatiques", 'icon': 'images/IT-guichet-icon.png', 'url': '/guichet/'},
        {'title': 'Wiki',                     'description': 'Base de connaissances collaborative',           'icon': 'images/wiki-icon.png',              'url': '/wiki/'},
        {'title': 'CRM',                      'description': 'Gestion de la relation client (contacts, affaires, interactions)', 'icon': 'images/crm-icon.png', 'url': '/crm/'},
        {'title': 'Ressources Humaines',       'description': 'Employés, contrats, congés, départements',                 'icon': 'images/hr-icon.png',              'url': '/rh/'},
        {'title': 'Gestion de projet ALM', 'description': 'Projets, exigences, tests, tickets', 'icon': 'images/Project-icon.png', 'url': '/projects/'},
        {'title': 'Blog Sécurité', 'description': 'Actualités et alertes sécurité', 'icon': 'images/Security-blog-icon.png', 'url': '/blog/securite/'},
        {'title': 'Blog Direction', 'description': 'Communications de la direction générale', 'icon': 'images/DG-blog-icon.png', 'url': '/blog/direction/'},
        {'title': 'Blog Communication', 'description': 'Informations et actualités', 'icon': 'images/com-blog-icon.png', 'url': '/blog/communication/'},
        {'title': 'Blog IT', 'description': 'Actualités techniques et IT', 'icon': 'images/IT-blog-icon.png', 'url': '/blog/it/'},
        {'title': 'Zone COMEX', 'description': "Espace d'échange du comité exécutif", 'icon': 'images/COMEX-exchange-zone-icon.png', 'url': '/comex/'},
    ]
    if request.user.is_staff:
        tiles.insert(0, {'title': 'Administration', 'description': 'Gestion des utilisateurs, fournisseurs, budgets', 'icon': 'images/Global-App-logo-icon.png', 'url': '/administration/'})
    return render(request, 'home.html', {'tiles': tiles})
