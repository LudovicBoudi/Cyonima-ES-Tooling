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
│   │   ├── blog_rep/       # Blog Représentation Syndicale
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
- `SecurityArticle`, `DirectionArticle`, `ComArticle`, `ITArticle`, `RepSyndicaleArticle` — articles de blog avec titre, contenu (HTML via CKEditor), image à la une, pièces jointes
- `ComexThread`, `ComexPost` — forum COMEX

### wiki
- `WikiPage` — titre, slug (auto-généré avec déduplication), contenu (HTML via CKEditor), auteur, timestamps

### crm
- `Company` — société (coordonnées, SIRET, secteur)
- `Contact` — contact rattaché à une société
- `Deal` — affaire avec pipeline (prospection → devis → négociation → gagné/perdu)
- `Interaction` — historique d'appels, emails, réunions, notes
- `CrmTask` — tâche liée à un contact ou une affaire, avec `reminder_date` (DateTimeField) et `reminder_sent` (BooleanField) — migration `crm/0002`
- `DealStageLog` — historique des changements d'étape (`from_stage`, `to_stage`, `changed_by`, `changed_at`) — migration `crm/0003`
- `CrmAttachment` — pièce jointe liée à `Deal` et `Interaction` — migration `crm/0004`

### hr
- `Employee` — fiche employé (coordonnées, département, poste, grade A1–I18, statut, dates, société prestataire)
- `Department` — département avec responsable
- `Contract` — contrat (CDI, CDD, stage…) avec dates et salaire
- `LeaveRequest` — demande de congé avec workflow (demandé → validé / refusé)
- `Diploma` — diplôme (niveau BEPC→Doctorat, nom, école, année, fichier)
- `Certification` — certification (nom, organisme émetteur, année, fichier)
- `Training` — formation (nom, organisme, année, fichier)
- `Employment` — historique d'emploi (titre, employeur, description, dates, durée calculée)
- `Cv` — CV (fichier PDF, date d'upload, validation extension + content-type)
- `Evaluation` — évaluation annuelle (année, note 1-5 colorisée, commentaire, évaluateur)

### erp
- `Quotation` — devis, identifiant `DEV-{seq:04d}`, JSONField lignes, + `deal` ForeignKey vers Deal (migration `erp/0002`)
- `Invoice` — facture, identifiant `FACT-{seq:04d}`, JSONField lignes
- `CreditNote` — avoir, identifiant `AVOIR-{seq:04d}`, JSONField lignes
- `SupplierInvoice` — facture fournisseur, identifiant `FACF-{seq:04d}`, JSONField lignes
- `Payment` — paiement, lie automatiquement le statut payée

### ged
- `DocumentCategory` — catégorie avec couleur
- `Document` — titre, fichier, statut (brouillon/en_relecture/publie/archive), version, tags, texte extrait (`content_text`), compteur téléchargements, `deleted_at` (soft-delete), numéro `DOC-{year}-{seq:05d}`
- `DocumentVersion` — version sauvegardée avant modification du fichier (file, version_number, notes, uploaded_by, uploaded_at)
- `SharedLink` — lien de partage public avec token UUID, expiration, actif/inactif
- `UserFavorite` — favori utilisateur + document (unique_together)
- `CategorySubscription` — abonnement utilisateur + catégorie (unique_together)
- `AuditLog` — journal d'audit (document, user, action, details, ip_address, created_at)

### analytics
- `PageView` — url, utilisateur, session_key, ip, user_agent, timestamp

### notifications
- `NotificationSetting` — préférences par utilisateur
- `Notification` — notification individuelle

### ressources
Pas de modèle — pages statiques servies par templates Django (RGPD, IGI 1300, IM 900, II 901, PCI DSS, NIS 2, EBIOS RM, IEC 62443, ISO 27001, ISO 27032, Convention Collective Métallurgie)

## URLs principales

| Chemin | Module |
|--------|--------|
| `/` | Accueil |
| `/accounts/` | Auth (login/logout/register) |
| `/administration/` | Admin custom |
| `/budget/` | Budget IT |
| `/guichet/` | Guichet IT |
| `/wiki/` | Wiki collaboratif |
| `/crm/` | CRM (dashboard, sociétés, contacts, affaires, interactions, tâches) |
| `/crm/exporter/societes/` | Export CSV sociétés |
| `/crm/exporter/contacts/` | Export CSV contacts |
| `/crm/exporter/affaires/` | Export CSV affaires |
| `/crm/importer/` | Import CSV sociétés/contacts |
| `/crm/pj/<pk>/` | Serve attachment |
| `/crm/pj/<pk>/supprimer/` | Delete attachment |
| `/rh/` | Ressources Humaines |
| `/rh/profil/` | Profil employé (6 onglets : diplômes, certifications, formations, emplois, CV, évaluations) |
| `/erp/` | ERP (devis, factures) |
| `/ged/` | GED (documents) — liste, catégories, favoris, corbeille, rapport d'audit |
| `/ged/ajouter/` | Ajouter un document |
| `/ged/<pk>/` | Détail du document |
| `/ged/<pk>/modifier/` | Modifier un document |
| `/ged/<pk>/supprimer/` | Déplacer vers la corbeille |
| `/ged/<pk>/restaurer/` | Restaurer depuis la corbeille |
| `/ged/<pk>/supprimer-definitivement/` | Supprimer définitivement |
| `/ged/<pk>/soumettre/` | Soumettre en relecture |
| `/ged/<pk>/approuver/` | Approuver / publier |
| `/ged/<pk>/archiver/` | Archiver |
| `/ged/<pk>/desarchiver/` | Désarchiver |
| `/ged/<pk>/telecharger/` | Télécharger |
| `/ged/<pk>/partager/` | Créer un lien de partage |
| `/ged/<pk>/favori/` | Ajouter/retirer des favoris |
| `/ged/partage/<uuid:token>/` | Page publique de partage |
| `/ged/mes-favoris/` | Liste des favoris |
| `/ged/corbeille/` | Corbeille |
| `/ged/rapport-audit/` | Rapport d'audit |
| `/ged/categories/` | Gestion des catégories (staff) |
| `/ged/categorie/<pk>/abonner/` | S'abonner/Se désabonner d'une catégorie |
| `/ressources/` | Ressources Externes (RGPD, PCI DSS, NIS 2, Conv. Métallurgie…) |
| `/projects/` | ALM |
| `/blog/securite/` | Blog sécurité |
| `/blog/direction/` | Blog direction |
| `/blog/communication/` | Blog communication |
| `/blog/it/` | Blog IT |
| `/blog/representation-syndicale/` | Blog Rep. Syndicale |
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

### CRM Pipeline (Deal)
```
Prospection → Devis → Négociation → Gagné
                                   → Perdu
```
Les changements d'étape sont journalisés dans `DealStageLog` (depuis le détail affaire et le Kanban drag & drop).

### CRM → ERP
```
Deal → « Créer un devis » → Quotation (avec lien deal)
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
- Contrôle d'accès aux blogs via `UserProfile.can_write_blog(code_role)` — admin toujours autorisé
- Accès aux projets via `Project.user_can_access()`
- Rôles multiples supportés (ManyToMany)
- `@hrbp_or_admin_required` décorateur pour les vues d'écriture RH (création, modification, suppression, validation congés)
- `can_view_salary` variable de contexte : visible uniquement pour `admin` et `hrbp`
- Blog Rep. Syndicale : écriture par `elus_syndicaux`, lecture par tous
