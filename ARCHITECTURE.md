# Architecture technique — Cyonima-ES-Tools

## Stack

| Composant | Technologie |
|-----------|-------------|
| Framework | Django 6.0.6 |
| Langage | Python 3.12 |
| Base de données | SQLite (développement) |
| CSS | Tailwind CSS (CDN) |
| Graphiques | Chart.js |
| Export PDF | WeasyPrint |
| Export XLSX | openpyxl |
| Serveur | runserver / Gunicorn + Nginx (prod) |
| Email | console (défaut), SMTP (prod) |

## Structure du projet

```
Cyonima-ES-Tooling/
├── apps/
│   ├── accounts/          # Authentification, profils, rôles, 2FA
│   ├── administration/    # Interface d'admin custom
│   ├── alm/               # Gestion de projet ALM
│   │   ├── projects/
│   │   ├── tickets/       # Incidents, tâches, FT
│   │   ├── requirements/
│   │   ├── tests/
│   │   ├── journal/
│   │   └── reports/
│   ├── backup/            # Commande de sauvegarde
│   ├── blogs/             # Blogs + COMEX
│   │   ├── sec_blog/
│   │   ├── dg_blog/
│   │   ├── blog_com/
│   │   ├── blog_it/
│   │   └── comex_forum/
│   ├── budget/            # Gestion budgétaire IT
│   │   ├── budgets/
│   │   ├── dashboard/
│   │   ├── dat/
│   │   ├── providers/
│   │   ├── todo/
│   │   └── guichet/       # Guichet IT (tickets incidents + EBI)
│   ├── core/              # Page d'accueil, SiteConfig
│   └── notifications/     # Système de notifications
├── config/
│   ├── urls.py            # Routage racine
│   └── settings.py        # Configuration Django
├── templates/             # Templates partagés
│   ├── budget/
│   ├── administration/
│   ├── alm/
│   ├── blogs/
│   └── ...
├── static/
│   ├── images/
│   └── css/
├── media/                 # Fichiers uploadés
├── images/                # Icônes sources
├── requirements.txt
└── ARCHITECTURE.md, DOCUMENTATION.md, README.md
```

## Modèles principaux

### accounts
- `UserProfile` — extension User (roles, 2FA, notifications)
- `Role` — code + label, lié en ManyToMany à UserProfile

### budget
- `BudgetYear` — enveloppe annuelle par type
- `DAT` — demande d'achat travaux, workflow statuts
- `DATLine` — ligne de produit dans une DAT
- `Provider` — fournisseur
- `TodoItem` — tâche Kanban
- `GuichetTicket` — ticket incident/EBI
- `GuichetLog` — historique des transitions guichet

### alm
- `Project` — projet avec membres
- `ProjectMember` — utilisateur + rôle dans un projet
- `Ticket` — ticket unifié (incident/tâche/FT) avec workflow
- `TicketLog` — historique des transitions
- `Requirement`, `TestScenario`, `TestCampaign`

### blogs
- `Article` — article de blog (présent dans chaque app blog)
- `ComexThread`, `ComexPost` — forum COMEX

### notifications
- `NotificationSetting` — préférences par utilisateur
- `Notification` — notification individuelle

## URLs principales

| Chemin | Module |
|--------|--------|
| `/` | Accueil |
| `/accounts/` | Auth (login/logout/register) |
| `/administration/` | Admin custom |
| `/budget/` | Budget IT |
| `/guichet/` | Guichet IT |
| `/projects/` | ALM |
| `/blog/securite/` | Blog sécurité |
| `/blog/direction/` | Blog direction |
| `/blog/communication/` | Blog communication |
| `/blog/it/` | Blog IT |
| `/comex/` | Forum COMEX |
| `/admin/` | Django admin |

## Workflows

### DAT
```
Brouillon → Soumise → Validée
                   → Rejetée
```

### Ticket ALM — Incident
```
Nouveau → Assigné → En cours → Clôturé
```

### Ticket ALM — Tâche
```
Nouveau → Assigné → En cours → Validé → Clôturé
```

### Guichet IT — Incident
```
Nouveau → En cours → Résolu → Fermé
```

### Guichet IT — EBI
```
Nouveau → En étude → Validé → Réalisé → Fermé
```

## Permissions

- `@login_required` sur toutes les vues
- `@staff_member_required` sur l'administration
- Contrôle d'accès aux blogs via `UserProfile.can_write_blog(code_role)`
- Accès aux projets via `Project.user_can_access()`
- Rôles multiples supportés (ManyToMany)
