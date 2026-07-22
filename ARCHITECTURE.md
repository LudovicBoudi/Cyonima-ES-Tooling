# Architecture — Cyonima-ES-Tools

## Stack technique

| Couche | Technologie |
|---|---|
| **Backend** | Django 6.0, Python 3.14 |
| **Base de données** | SQLite (dev), PostgreSQL/MySQL (prod) |
| **Frontend** | Tailwind CSS (CDN), Alpine.js, Chart.js, CKEditor 5 |
| **PDF/Excel** | WeasyPrint, openpyxl |
| **Sécurité HTML** | BeautifulSoup4 (sanitizer) |
| **Déploiement** | Docker, docker-compose, GitHub Actions → ghcr.io |

## Structure du projet

```
Cyonima-ES-Tooling/
├── apps/                          # Applications Django
│   ├── core/                      # Page d'accueil, configuration, context processors
│   ├── accounts/                  # Authentification, profils, rôles (ManyToMany), 2FA
│   ├── administration/            # Panel admin : utilisateurs, backup, analytics
│   ├── budget/
│   │   ├── budgets/               # Enveloppes budgétaires annuelles
│   │   ├── dat/                   # Demandes d'Achat Travaux + modèles DAT
│   │   ├── dashboard/             # Tableau de bord budgétaire + alertes
│   │   ├── guichet/               # Guichet IT (incidents/EBI)
│   │   ├── providers/             # Fournisseurs
│   │   └── todo/                  # Kanban tâches
│   ├── alm/
│   │   ├── projects/              # Projets + membres
│   │   ├── requirements/          # Exigences (arborescence)
│   │   ├── tests/                 # Scénarios de test + campagnes
│   │   ├── tickets/               # Tickets (incidents/tâches/FT), sprints, releases
│   │   ├── journal/               # Journal + audit
│   │   ├── reports/               # Rapport temps
│   │   └── repositories/          # Dépôts Git (subprocess)
│   ├── blogs/                     # 5 blogs (sécurité, direction, com, IT, syndical)
│   ├── crm/                       # Sociétés, contacts, affaires (pipeline), interactions
│   ├── hr/                        # Employés, contrats, congés, diplômes, organigramme
│   ├── erp/                       # Devis, factures, avoirs, paiements, récurrentes
│   ├── ged/                       # Documents, catégories, workflow, versionnage
│   ├── portal/                    # Portail self-service (devis/factures, mon compte, notifs)
│   ├── favorites/                 # Favoris global transversal (21 modèles)
│   ├── wiki/                      # Pages wiki (CKEditor)
│   ├── notifications/             # Notifications in-app + email
│   ├── analytics/                 # Web analytics (middleware)
│   ├── backup/                    # Sauvegarde CLI
│   └── ressources/                # Pages réglementaires statiques
├── config/                        # Configuration Django
│   ├── settings.py                # Django settings
│   ├── urls.py                    # Routage racine
│   └── wsgi.py                    # Point d'entrée WSGI
├── templates/                     # Templates HTML (Django templates)
│   ├── base.html                  # Layout principal + dark mode + messages
│   ├── home.html                  # Page d'accueil (tuiles + activité)
│   ├── alm/                       # Templates ALM
│   ├── budget/                    # Templates Budget
│   ├── crm/, erp/, hr/, ged/      # Templates par module
│   ├── blogs/, wiki/              # Templates blogs et wiki
│   ├── notifications/             # Templates notifications
│   └── ressources/                # Pages réglementaires
├── static/                        # Fichiers statiques (images)
├── media/                         # Fichiers utilisateurs (upload)
├── img-doc/                       # Captures d'écran documentation
├── .github/                       # CI/CD, templates, dependabot
├── .devcontainer/                 # Configuration Codespaces
├── Dockerfile                     # Build image Docker
├── docker-compose.yml             # Orchestration Docker
├── docker-entrypoint.sh           # Script démarrage (migrations + run)
├── requirements.txt               # Dépendances Python
├── .env.example                   # Variables d'environnement template
├── README.md                      # Documentation principale
├── DOCUMENTATION.md               # Documentation utilisateur
└── ARCHITECTURE.md                # Ce fichier
```

## Rôles et permissions

Les rôles sont gérés via `UserProfile.roles` (ManyToMany → `Role`). 8 rôles disponibles :

| Code | Accès |
|---|---|
| `admin` | Tout (administration, blogs, projets, COMEX) |
| `it_manager` | Budget IT, Guichet IT, blog IT |
| `direction` | Blog direction, COMEX |
| `security_officer` | Blog sécurité |
| `communication` | Blog communication |
| `hrbp` | RH (écriture, validation congés, salaires) |
| `elus_syndicaux` | Blog syndical |
| `user` | Base (lecture) |

La méthode `UserProfile.can_write_blog(blog_type)` centralise les permissions blogs.

## Modèles de données clés

### Workflow tickets (ALM)
```
Incident : nouveau → assigne → en_cours → cloture
Tâche    : nouveau → assigne → en_cours → valide → cloture
FT       : nouveau → assigne → en_cours → valide → a_clore → cloture
```

### Workflow DAT (Budget)
```
Brouillon → Soumise → Validée / Rejetée
```

### Workflow validation (GED)
```
Brouillon → En relecture → Publié → Archivé
```

### Pipeline CRM
```
Prospection → Devis → Négociation → Gagné / Perdu
```

### Favoris global
- Modèle `UserFavorite` (user, app_label, model_name, object_id) — generic FK.
- Registry de 21 modèles supportés dans `apps/favorites/registry.py`.
- Bouton ☆/★ via template tag `{% favorite_button %}`.

### Portail self-service
- Comptes portail liés aux contacts CRM (`Contact.is_portal_user`).
- Notifications in-app sur événements devis/factures/avoirs (signaux Django).

## URLs principales

| Module | URL racine |
|---|---|
| Administration | `/administration/` |
| Budget IT | `/budget/` |
| Guichet IT | `/guichet/` |
| ALM | `/projects/` |
| ALM Dashboard | `/alm/dashboard/` |
| Blogs | `/blog/securite/`, `/blog/direction/`, etc. |
| Accueil blogs | `/blog/` |
| Wiki | `/wiki/` |
| CRM | `/crm/` |
| CRM Portail admin | `/crm/portail/` |
| RH | `/rh/` |
| ERP | `/erp/` |
| GED | `/ged/` |
| GED Documents récents | `/ged/recents/` |
| Portail self-service | `/portail/` |
| Favoris global | `/favoris/` |
| Ressources | `/ressources/` |
| COMEX | `/comex/` |
| Notifications | `/notifications/` |
| Recherche globale | `/recherche/` |

## Sécurité

- **SECRET_KEY** : variable d'environnement obligatoire
- **Production** : CSRF/HSTS/SSL activés hors DEBUG
- **Sanitizer HTML** : BeautifulSoup4 sur wiki + blogs
- **CSRF** : tous les formulaires + AJAX
- **POST obligatoire** : mutations (congés, suppressions, notifications)
- **Middleware HTTPS** : redirection HTTP→HTTPS + HSTS configurable

## Déploiement

### Docker
```bash
docker compose up -d         # Premier lancement
docker compose pull && up -d # Mise à jour
```

L'image est publiée sur `ghcr.io/ludovicboudi/cyonima-es-tooling` via GitHub Actions à chaque push sur `main`.

### Codespaces
Ouverture en 1 clic : environnement Python 3.14 préconfiguré, dépendances installées, migrations exécutées.

### Commandes utiles
```bash
python manage.py check_budget_alerts   # Alertes seuils budgétaires
python manage.py notify_deadlines      # Notifications échéances tickets
python manage.py check_expiry           # Alertes expiration documents GED
python manage.py generate_recurring     # Génération factures récurrentes
python manage.py daily_digest          # Résumé quotidien email
python manage.py auto_reminders        # Relances automatiques factures impayées > 30j
python manage.py cyonima_backup        # Sauvegarde (ZIP)
```
