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
│   ├── wiki/              # Wiki collaboratif
│   ├── crm/               # CRM (contacts, affaires, interactions)
│   ├── hr/                # RH (employés, contrats, congés)
│   ├── budget/            # Gestion budgétaire IT
│   │   ├── budgets/
│   │   ├── dashboard/
│   │   ├── dat/
│   │   ├── providers/
│   │   ├── todo/
│   │   └── guichet/       # Guichet IT (tickets incidents + EBI)
│   ├── analytics/         # Web Analytics (middleware + dashboard)
│   ├── erp/               # Devis, factures, avoirs, paiements
│   ├── ged/               # GED — documents avec catégories, tags
│   ├── ressources/        # Pages statiques réglementaires (RGPD, PCI DSS…)
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
│   ├── wiki/
│   ├── crm/
│   ├── hr/
│   ├── erp/
│   ├── ged/
│   ├── ressources/
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
- `SecurityArticle`, `DirectionArticle`, `ComArticle`, `ITArticle` — articles de blog avec titre, contenu (HTML via CKEditor), image à la une, pièces jointes
- `ComexThread`, `ComexPost` — forum COMEX

### wiki
- `WikiPage` — titre, slug (auto-généré avec déduplication), contenu (HTML via CKEditor), auteur, timestamps

### crm
- `Company` — société (coordonnées, SIRET, secteur)
- `Contact` — contact rattaché à une société
- `Deal` — affaire avec pipeline (prospection → devis → négociation → gagné/perdu)
- `Interaction` — historique d'appels, emails, réunions, notes
- `CrmTask` — tâche liée à un contact ou une affaire

### hr
- `Employee` — fiche employé (coordonnées, département, poste, statut, dates)
- `Department` — département avec responsable
- `Contract` — contrat (CDI, CDD, stage…) avec dates et salaire
- `LeaveRequest` — demande de congé avec workflow (demandé → validé / refusé)

### erp
- `Quotation` — devis, identifiant `DEV-{seq:04d}`, JSONField lignes
- `Invoice` — facture, identifiant `FACT-{seq:04d}`, JSONField lignes
- `CreditNote` — avoir, identifiant `AVOIR-{seq:04d}`, JSONField lignes
- `SupplierInvoice` — facture fournisseur, identifiant `FACF-{seq:04d}`, JSONField lignes
- `Payment` — paiement, lie automatiquement le statut payée

### ged
- `DocumentCategory` — catégorie avec couleur
- `Document` — titre, fichier, version, tags, compteur téléchargements, numéro `DOC-{year}-{seq:05d}`

### analytics
- `PageView` — url, utilisateur, session_key, ip, user_agent, timestamp

### notifications
- `NotificationSetting` — préférences par utilisateur
- `Notification` — notification individuelle

### ressources
Pas de modèle — pages statiques servies par templates Django (RGPD, IGI 1300, IM 900, II 901, PCI DSS, NIS 2)

## URLs principales

| Chemin | Module |
|--------|--------|
| `/` | Accueil |
| `/accounts/` | Auth (login/logout/register) |
| `/administration/` | Admin custom |
| `/budget/` | Budget IT |
| `/guichet/` | Guichet IT |
| `/wiki/` | Wiki collaboratif |
| `/crm/` | CRM |
| `/rh/` | Ressources Humaines |
| `/erp/` | ERP (devis, factures) |
| `/ged/` | GED (documents) |
| `/ressources/` | Ressources Externes (RGPD, PCI DSS, NIS 2…) |
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

### ERP
```
Devis (DEV) → converti → Facture (FACT)
Paiement → statut facture passe en « payée »
```

### Leave Request
```
Demandée → Validée
        → Refusée
```

### Contrat (couleurs)
- CDI : vert (permanent)
- CDD / Mission : vert (>3mo), jaune (1-3mo), orange (<1mo), rouge (<1sem ou expiré)

## Permissions

- `@login_required` sur toutes les vues
- `@staff_member_required` sur l'administration
- Contrôle d'accès aux blogs via `UserProfile.can_write_blog(code_role)`
- Accès aux projets via `Project.user_can_access()`
- Rôles multiples supportés (ManyToMany)
