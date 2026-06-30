# CCTP => Objet du projet, description et exigences

## Objet du projet

Création d'une WebApp Python + Django permettant de gérer la plupart des tâches liées à l'IT d'une petite entreprise ou d'un GIE.

## fonctionnalités :

Ensemble des fonctionalités attendues de cette WebApp.

### 1/ Gestion budgétaire IT :

#### 1.1/ présentation

Permet de suivre les enveloppes budgétaires (Investissement / Fonctionnement), gérer les fournisseurs, créer des demandes d'achat et de travaux(DAT) et visualiser la consommation en temps réel.

- **Budgets** — Définition annuelle des budgets Investissement et Fonctionnement
- **Fournisseurs** — Registre des fournisseurs validés
- **DAT** — "Demande d'achat et travaux" avec ID auto-incrémenté (`IT-XXXX-2026`), lignes de produits, calcul automatique des totaux
- **Duplication** — Copie d'une DAT existante avec les lignes et un nouvel ID
- **Dashboard** — Graphiques de consommation budgétaire par catégorie (Chart.js), évolution multi-années (Investissement / Fonctionnement), alertes à 80 % et 100 %
- **Export** — PDF (weasyprint), XLSX (OpenXML avec mise en forme), CSV (liste complète)
- **Recherche & filtres** — Filtres par texte, fournisseur, année, montant et statut avec pagination conservée
- **Tâches (Todo)** — Tableau Kanban avec drag & drop et colorimétrie par échéance
- **Logo personnalisable** — Upload via l'interface d'administration
- **Sauvegarde / Restauration** — Export et import JSON de l'intégralité des données
- **Configuration externalisée** — Variables sensibles dans `.env` (SECRET_KEY, DEBUG, DATABASE_URL)

#### 1.2/ Profils et permissions

##### 1.2.1 Rôles

| Rôle | Code | Accès |
|------|------|-------|
| **Administrateur** | `admin` | CRUD complet sur toutes les entités, workflow, exports, sauvegarde/restauration, gestion des utilisateurs |
| **Gestionnaire IT** | `admin` | CRUD complet sur toutes les entités, workflow, exports |
| **Contrôleur de gestion** | `controller` | Lecture seule sur le dashboard et les dat |

##### 1.2.2 Règles

- Le rôle est stocké sur `UserProfile` (OneToOneField vers `auth.User`), créé automatiquement via `post_save` signal.
- Un mixin `ControllerReadOnlyMixin` bloque les accès en écriture pour les contrôleurs (redirection + message).
- Un `AdminRequiredMixin` réserve l'accès aux administrateurs.
- Le logout exige une requête POST (CSRF protégé).

---

#### 1.3. Modules fonctionnels

##### 1.3.1 Fournisseurs (`providers`)

**Modèle `Provider`** :
- `company_name` — Nom de l'entreprise (255 chars)
- `sales_contact` — Contact commercial (255 chars)
- `phone` — Téléphone (50 chars)
- `email` — Email
- `description` — Texte libre (optionnel)
- `created_at` / `updated_at` — Timestamps auto

CRUD réservé aux administrateurs.

##### 1.3.2 Budgets (`budgets`)

**Modèle `BudgetYear`** :
- `year` — Année (Integer)
- `budget_type` — Choix : `investment` (Investissement) / `fonctionnement` (Fonctionnement)
- `amount` — Montant alloué (Decimal 12,2, ≥ 0)
- Unique ensemble : `(year, budget_type)`

CRUD réservé aux administrateurs.

##### 1.3.3 DAT

Cœur métier de cette partie de l'application.

###### Modèle `DAT`

**Champs** :
- `status` — Choix : `draft` (Brouillon, défaut), `submitted` (Soumis), `validated` (Validé), `rejected` (Refusé)
- `sequence_number` — Auto-incrémenté par année (editable=False)
- `year` — Année en cours à la création (editable=False)
- `created_date` — Date de création (auto_now_add)
- `description` — Texte libre
- `provider` — FK vers `Provider` (on_delete=PROTECT)
- `provider_contact_name`, `provider_contact_email`, `provider_contact_phone` — Coordonnées du contact fournisseur
- `created_at` / `updated_at` — Timestamps auto

**Contraintes** :
- ID affiché : `IT-{sequence_number:04d}-{year}` (ex: `IT-0001-2026`)
- `unique_together = [sequence_number, year]`
- `ordering = [-year, -sequence_number]`

**Logique métier** :
- `save()` : à la création, calcule `year` avec `timezone.now().year` et `sequence_number` en incrémentant le dernier de l'année (ou 1 si premier)
- `total_cost()` : agrège `SUM(lines__global_price)`
- `consumption_by_category()` : dictionnaire `{(budget_type, category): total}` pour les lignes non nulles
- `duplicate()` : copie l'dat (sans les lignes, puis les recrée) avec un nouveau numéro de séquence et statut `draft`

**Workflow d'approbation** :

| Depuis | Action | Vers | Conditions |
|--------|--------|------|------------|
| Brouillon | Soumettre | Soumis | Admin uniquement |
| Soumis | Valider | Validé | Admin uniquement |
| Soumis | Refuser | Refusé | Admin uniquement |
| Soumis | Repasser en brouillon | Brouillon | Admin uniquement |
| Refusé | Repasser en brouillon | Brouillon | Admin uniquement |
| Validé (ou Refusé) | Modifier | Bloqué | Message d'erreur + redirection |
| Validé (ou Refusé) | Supprimer | Bloqué | Message d'erreur + redirection |

###### Modèle `DATLine`

**Champs** :
- `dat` — FK vers `dat` (CASCADE, related_name="lines")
- `product` — Nom du produit (255 chars)
- `reference` — Référence fournisseur (255 chars, optionnel)
- `unit` — Unité : `U` (Unité) / `D` (Jour)
- `quantity` — Quantité (Integer, ≥ 1)
- `unit_price` — Prix unitaire (Decimal 10,2, ≥ 0)
- `global_price` — Total ligne = `quantity × unit_price` (Decimal 12,2, calculé, editable=False)
- `budget_type` — `investment` / `fonctionnement`
- `budget_category` — `licences`, `maintenance`, `pc`, `servers`, `network`, `security`, `consulting`

**Logique métier** :
- `save()` : calcule `global_price = quantity × unit_price`

##### 1.3.3 Dashboard (`dashboard`)

###### Vue principale

- Sélecteur d'année (basé sur les `BudgetYear` existants)
- Affichage par type de budget (Investissement / Fonctionnement) :
  - Barre de progression (alloué vs consommé) avec code couleur : vert (< 80 %), orange (80–100 %), rouge (≥ 100 %)
  - Alerte-bannière par catégorie : idem seuils 80 % / 100 %
  - Graphique doughnut (Chart.js) : répartition par catégorie, centré sur le montant alloué vs consommé
  - Tableau ventilé : catégorie, montant consommé, pourcentage, indicateur de statut

###### Évolution multi-années

- Graphique en courbes (line chart, Chart.js) avec 4 datasets :
  - Investissement alloué
  - Investissement consommé
  - Run alloué
  - Run consommé
- Ordonnée : montant en euros
- Abscisse : années disponibles (tri croissant)

##### 1.3.4 Exports (`DAT`)

| Format | Déclencheur | Technologie | Contenu |
|--------|-------------|-------------|---------|
| **PDF** | Bouton sur la page détail | WeasyPrint (HTML → PDF) | Document A4 : en-tête dat, tableau des lignes, total |
| **XLSX** | Bouton sur la page détail | OpenPyXL | Fichier formaté : en-tête bleu (#1A3A6B), nombres formatés `#,##0.00`, ligne Total |
| **CSV** | Bouton sur la liste | `csv` standard | UTF-8 BOM, tous les dat avec leurs lignes (une ligne par ligne) |

##### 1.3.5 Recherche et filtres dat (`DAT`)

La liste des dat propose un formulaire de filtrage (GET) avec les champs suivants :

- `q` — Recherche texte libre (description, fournisseur, nom du contact)
- `provider` — Sélecteur déroulant (tous les fournisseurs)
- `year_from` / `year_to` — Plage d'années
- `amount_min` / `amount_max` — Plage de montants (filtre sur `computed_total` annoté avec `Coalesce(Sum(lines__global_price), 0)`)
- `status` — Filtre par statut

Tous les filtres sont conservés dans l'URL lors de la pagination.

##### 1.3.6 Tâches Kanban (`todo`)

**Modèle `TodoItem`** :
- `title` — Titre (255 chars)
- `description` — Texte libre (optionnel)
- `deadline` — Date limite
- `status` — `todo` (À faire), `in_progress` (En cours), `done` (Réalisé)
- `order` — Ordre d'affichage (Integer, défaut 0)

**Affichage** : tableau en 3 colonnes (todo → in_progress → done) avec drag & drop AJAX (mise à jour du statut et de l'ordre).

**Colorimétrie des deadlines** :
- `safe` (vert) : > 7 jours restants
- `warning` (orange) : ≤ 7 jours
- `critical` (rouge) : le jour même
- `overdue` (gris foncé) : deadline dépassée
- `done` (gris clair) : tâche réalisée (quel que soit le délai)

##### 1.3.7 Configuration du site (`siteconfig`)

Singleton `SiteConfig` (pk=1) :
- `site_name` — Nom du site (100 chars, défaut "Gestion IT")
- `logo` — Image uploadée (logos/, recommandé 120×40 px, PNG/SVG)

Un context processor injecte `site_config` dans tous les templates. Logo par défaut : SVG inline (lettre "C" stylisée).

##### 1.3.8 Utilisateurs (`accounts`)

- Vue de création d'utilisateur (admin uniquement) : username + mot de passe + sélection du rôle
- Changement de mot de passe (admin) : page Django standard
- `UserProfile` créé automatiquement via signal `post_save`

**Validation des mots de passe** :
- Minimum 12 caractères
- Au moins une majuscule, une minuscule, un chiffre, un caractère spécial
- Pas de similarité avec l'utilisateur
- Pas de mot de passe trop commun
- Pas que des chiffres

##### 1.3.9 Sauvegarde / Restauration

- **Sauvegarde** : `dumpdata` JSON → téléchargement d'un fichier `.json`
- **Restauration** : upload d'un fichier `.json` → `loaddata`
- Réservé aux administrateurs, accessible depuis le menu "Sauvegarde"



#### 1.4. Interface utilisateur

##### 1.4.1 Charte graphique

- Navbar : bleu royal `#1a3a6b`
- Fond de page : gris clair `#f0f2f5`
- Cartes : blanc avec ombre légère (Bootstrap `card`)
- Format monétaire : français (1 700 000,00 €) via filtre template personnalisé

##### 1.4.2 Pages

| Route | Template | Description |
|-------|----------|-------------|
| `/` ou `/{lang}/dashboard/` | `dashboard/dashboard.html` | Dashboard + évolution multi-années |
| `/{lang}/dat/` | `dat/dat_list.html` | Liste avec filtres et pagination |
| `/{lang}/dat/nouveau/` | `dat/dat_form.html` | Création avec formset dynamique |
| `/{lang}/dat/<pk>/` | `dat/dat_detail.html` | Détail avec boutons PDF/XLSX/workflow/duplication |
| `/{lang}/dat/<pk>/modifier/` | `dat/dat_form.html` | Modification (bloqué si validé/refusé) |
| `/{lang}/dat/<pk>/supprimer/` | `dat/dat_confirm_delete.html` | Confirmation suppression (bloqué si validé/refusé) |
| `/{lang}/providers/` | CRUD générique | Gestion des fournisseurs |
| `/{lang}/budgets/` | CRUD générique | Gestion des budgets |
| `/{lang}/todo/` | `todo/board.html` | Kanban drag & drop |
| `/{lang}/aide/` | `help.html` | Page d'aide |
| `/{lang}/sauvegarde/` | Formulaire | Export/import JSON |
| `/{lang}/users/` | Formulaire | Création d'utilisateur |
| `/admin/` | Django admin | Interface d'administration |

---

### 2/ Gestion de projet interne :
Application de gestion du cycle de vie (ALM) — Fusion des concepts de **Redmine** et **HP Quality Center**.

---

#### 2.1. Présentation générale

#### 2.1.1 Objectif
Application web de gestion de cycle de vie applicative permettant de suivre les **exigences**, **tests**, **campagnes de test**, **tickets** (incidents/tâches/faits techniques), la **traçabilité** entre exigences et tests, le **journal d'activité**, et les **rapports temps**, le tout dans un cadre projet avec gestion des **membres** et **rôles**.

#### 2.1.2 Architecture
- Monolithique Django, montée en modules (*apps*)
- URLs prefixées par projet : `/projects/<id>/...`
- Template de base avec sidebar projet (8 entrées)
- Authentification requise sur toutes les pages (sauf login)

---

### 2.2. Modules fonctionnels

#### 2.2.1 Comptes utilisateurs — `apps.accounts`

| Rôle | Code | Accès |
|------|------|-------|
| **Administrateur** | `admin` | accés complet |
| **Utilisateur** | `user` | peut créer des projets |

Lorsqu'un "Utilisateur" crée un projet il en devient automatiquement le "Chef de projet" et peut en administrer le contenu et y inviter des utilisateurs avec des rôles précis

**Vues :**
| URL | Nom | Description |
|-----|-----|-------------|
| `/accounts/login/` | `login` | Connexion (email + mot de passe) |
| `/accounts/logout/` | `logout` | Déconnexion |
| `/accounts/password/` | `password_change` | Changement de mot de passe |
| `/accounts/users/` | `user_list` | Liste des utilisateurs (admin seulement) |
| `/accounts/users/create/` | `user_create` | Création d'utilisateur (admin seulement) |

**Filtre d'accès :** `user_can_access()` sur chaque projet → `is_admin` OU membre du projet.
Messages flash d'erreur en cas de refus, redirection vers la liste des projets.

---

#### 2.2.2 Projets et membres — `apps.projects`

**Modèle : `Project`**
- `name`, `description`, `created_by` (FK User), `created_at`, `updated_at`
- `user_is_member(user)` → booléen
- `user_can_access(user)` → `user.is_admin or user_is_member(user)`

**Modèle : `ProjectMember`**
- `project` (FK), `user` (FK), `role`, `joined_at`
- `unique_together = (project, user)`
- Rôles : `chef_projet`, `developpeur`, `testeur`, `integrateur`

**Vues :**
| URL | Nom | Description |
|-----|-----|-------------|
| `/projects/` | `project_list` | Liste des projets accessibles |
| `/projects/create/` | `project_create` | Création |
| `/projects/<id>/` | `project_detail` | Tableau de bord |
| `/projects/<id>/edit/` | `project_edit` | Modification |
| `/projects/<id>/members/` | `member_list` | Liste des membres |
| `/projects/<id>/members/add/` | `member_add` | Ajout membre |
| `/projects/<id>/members/<mid>/remove/` | `member_remove` | Retrait membre |

**Navigation sidebar :** 8 entrées — Tableau de bord, Membres, Exigences, Tests, Campagnes, Tickets, Traçabilité, Journal, Rapport temps.

---

#### 2.2.3 Exigences — `apps.requirements`

**Modèle : `Requirement`**
- `project` (FK), `parent` (FK self, nullable), `number` (auto), `category`, `name`, `description` (max 4000), `created_at`, `updated_at`
- Catégories : `folder`, `metier`, `infrastructure`, `logiciel`, `securite`, `reseau`, `administration`
- `unique_together = (project, number)` — numérotation automatique par projet
- `get_formatted_number` → `D-XXXX` si dossier, `XXXX` sinon
- `save()` : auto-incrémente `number` si non défini
- `get_children_tree()` : parcours récursif descendant

**Modèle : `RequirementAttachment`**
- `requirement` (FK), `file` (FileField), `filename`, `uploaded_by` (FK User), `uploaded_at`
- Stockage : `requirements/<project_id>/<req_id>/`

**Vues :**
| URL | Nom | Description |
|-----|-----|-------------|
| `/projects/<id>/requirements/` | `requirement_list` | Vue arborescente avec indentation |
| `/projects/<id>/requirements/create/` | `requirement_create` | Création |
| `/projects/<id>/requirements/<rid>/edit/` | `requirement_edit` | Modification + pièces jointes |
| `/projects/<id>/requirements/<rid>/delete/` | `requirement_delete` | Suppression |
| `/projects/<id>/requirements/<rid>/attachments/upload/` | `requirement_upload_attachment` | Upload fichier |
| `/projects/<id>/requirements/<rid>/attachments/<aid>/delete/` | `requirement_delete_attachment` | Suppression pièce jointe |
| `/projects/<id>/requirements/export/csv/` | `requirement_export_csv` | Export CSV (BOM UTF-8) |
| `/projects/<id>/traceability/` | `traceability_matrix` | Matrice de traçabilité |
| `/projects/<id>/traceability/export/csv/` | `traceability_export_csv` | Export CSV traçabilité |
| `/projects/<id>/traceability/export/pdf/` | `traceability_export_pdf` | Export PDF traçabilité (WeasyPrint) |

**Formulaire `RequirementForm` :**
- Champs : `category`, `name`, `parent`, `description`
- `parent` filtré aux exigences de catégorie `folder` du projet courant
- Exclut l'instance en cours de modification de la liste des parents

**Règles métier :**
- Les dossiers (`category=folder`) sont des conteneurs, pas des exigences fonctionnelles
- Seules les exigences (non-dossiers) apparaissent dans le nombre total de la traçabilité
- L'arbre utilise une fonction `build_requirement_tree()` qui flatte récursivement avec un niveau d'indentation

---

#### 2.2.4 Tests — `apps.tests`

**Modèle : `TestScenario`**
- `project` (FK), `number` (auto), `name`, `execution_conditions`, `description`, `requirements` (M2M Requirement), `created_at`, `updated_at`
- `unique_together = (project, number)` — numérotation auto par projet
- `get_formatted_number` → `XXXX`

**Modèle : `TestStep`**
- `test_scenario` (FK), `step_number`, `action`, `expected_result`
- `unique_together = (test_scenario, step_number)` — max 10 étapes
- Tri par `step_number`

**Modèle : `TestCampaign`**
- `project` (FK), `name`, `description`, `created_at`, `updated_at`

**Modèle : `CampaignTest`**
- `campaign` (FK), `test_scenario` (FK), `status`, `position`
- `unique_together = (campaign, test_scenario)`
- Statuts : `backlog`, `en_cours`, `verifie`, `valide`

**Modèle : `TestAttachment`**
- `test_scenario` (FK), `file`, `filename`, `uploaded_by` (FK User), `uploaded_at`
- Stockage : `tests/<project_id>/<test_id>/`

**Vues :**
| URL | Nom | Description |
|-----|-----|-------------|
| `/projects/<id>/tests/` | `test_list` | Liste des scénarios |
| `/projects/<id>/tests/create/` | `test_create` | Création (avec 10 étapes inline) |
| `/projects/<id>/tests/<tid>/edit/` | `test_edit` | Modification + pièces jointes |
| `/projects/<id>/tests/<tid>/delete/` | `test_delete` | Suppression |
| `/projects/<id>/tests/<tid>/attachments/upload/` | `test_upload_attachment` | Upload fichier |
| `/projects/<id>/tests/<tid>/attachments/<aid>/delete/` | `test_delete_attachment` | Suppression pièce jointe |
| `/projects/<id>/campaigns/` | `campaign_list` | Liste des campagnes |
| `/projects/<id>/campaigns/create/` | `campaign_create` | Création campagne |
| `/projects/<id>/campaigns/<cid>/` | `campaign_detail` | Kanban 4 colonnes |
| `/projects/<id>/campaigns/<cid>/update-status/` | `campaign_update_status` | AJAX drag & drop |
| `/projects/<id>/campaigns/<cid>/add-tests/` | `campaign_add_tests` | Ajout tests à la campagne |
| `/projects/<id>/campaigns/<cid>/delete/` | `campaign_delete` | Suppression campagne |

**Kanban :**
- 4 colonnes : Backlog, En cours, Vérifié, Validé
- Drag & drop via SortableJS
- Mise à jour AJAX (POST JSON → `campaign_update_status`)
- Changement côté serveur : `CampaignTest.status` + `position`

---

#### 2.2.5 Tickets — `apps.tickets`

**Modèle : `Ticket`**
- `project` (FK), `ticket_type`, `number` (auto), `title`, `description`, `assigned_to` (FK User nullable), `status`, `start_date` (DateField nullable), `due_date` (DateField nullable), `created_by` (FK User), `created_at`, `updated_at`
- `unique_together = (project, ticket_type, number)` — numérotation auto par projet+type
- `get_type_prefix` → `INC`, `TCH`, `FT`
- `get_formatted_number` → `INC-0001`, `TCH-0001`, `FT-0001`
- `get_available_statuses()` → statuts du type courant
- `save()` : auto-incrémente `number` par projet+type, définit `status='nouveau'` par défaut

**Modèle : `TicketLog`**
- `ticket` (FK), `user` (FK), `from_status`, `to_status`, `comment`, `hours_spent` (Decimal max 6.1), `created_at`
- Tri inverse par `created_at`

**Modèle : `TicketAttachment`**
- `ticket` (FK), `file`, `filename`, `uploaded_by` (FK User), `uploaded_at`
- Stockage : `tickets/<project_id>/<ticket_id>/`

**Types de tickets et workflows (transitions autorisées) :**

**Incident** (4 statuts) :
```
nouveau → assigne → en_cours → cloture
```
Transitions : `nouveau→[assigne]`, `assigne→[en_cours, nouveau]`, `en_cours→[cloture, assigne]`, `cloture→[]`

**Tâche** (5 statuts) :
```
nouveau → assigne → en_cours → valide → cloture
```
Transitions : `nouveau→[assigne]`, `assigne→[en_cours, nouveau]`, `en_cours→[valide, assigne]`, `valide→[cloture, en_cours]`, `cloture→[]`

**Fait technique** (6 statuts) :
```
nouveau → assigne → en_cours → valide → a_clore → cloture
```
Transitions : `nouveau→[assigne]`, `assigne→[en_cours, nouveau]`, `en_cours→[valide, assigne]`, `valide→[a_clore, en_cours]`, `a_clore→[cloture, valide]`, `cloture→[]`

**Vues :**
| URL | Nom | Description |
|-----|-----|-------------|
| `/projects/<id>/tickets/` | `ticket_list` | Liste filtrée par type |
| `/projects/<id>/tickets/create/` | `ticket_create` | Création |
| `/projects/<id>/tickets/<tid>/` | `ticket_detail` | Détail + historique + transition |
| `/projects/<id>/tickets/<tid>/attachments/upload/` | `ticket_upload_attachment` | Upload fichier |
| `/projects/<id>/tickets/<tid>/attachments/<aid>/delete/` | `ticket_delete_attachment` | Suppression pièce jointe |
| `/projects/<id>/tickets/kanban/` | `ticket_kanban` | Kanban par type |
| `/projects/<id>/tickets/gantt/` | `ticket_gantt` | Diagramme de Gantt |
| `/projects/<id>/tickets/export/csv/` | `ticket_export_csv` | Export CSV |

**Détail ticket :**
- Affichage du ticket (type, titre, statut, assigné, dates)
- Bandes de couleur : rouge (incident), bleu (tâche), violet (fait technique)
- Section d'historique (TicketLog) : chaque ligne montre statut précédent → nouveau + commentaire + heures + utilisateur
- Formulaire de transition : sélecteur de statut (transitions autorisées) + commentaire + heures
- Section pièces jointes (upload / suppression)
- Bouton retour vers Kanban

**Diagramme de Gantt :**
- Barres proportionnelles à la durée
- En-têtes : mois + semaines (format `jj/mm`)
- Ligne verticale "Aujourd'hui"
- Filtre par type de ticket
- Calcul : `start_date` ou `created_at`, `due_date` ou `start_date + 7 jours`
- Formule CSS : `left: X%; width: Y%` basée sur le nombre total de jours

---

#### 2.2.6 Journal d'activité — `apps.journal`

**Modèle : `ActivityReport`**
- `project` (FK), `user` (FK), `report_date` (DateField), `content` (TextField), `created_at`, `updated_at`
- Tri : `[-report_date, -created_at]`

**Vues :**
| URL | Nom | Description |
|-----|-----|-------------|
| `/projects/<id>/journal/` | `journal_list` | Liste des comptes rendus |
| `/projects/<id>/journal/create/` | `journal_create` | Création |

---

#### 2.2.7 Rapports temps — `apps.reports`

**Vue :**
| URL | Nom | Description |
|-----|-----|-------------|
| `/projects/<id>/reports/time/` | `time_report` | Rapport temps |

**Fonctionnalités :**
- Agrégation depuis `TicketLog.hours_spent`
- Filtres : période (start_date, end_date), utilisateur, type de ticket
- Totaux : heures totales, par utilisateur, par type
- Dernières 50 saisies (tableau récent)
- Lien dans la sidebar : "Rapport temps"

---

#### 2.2.8 Traçabilité — `apps.requirements` (intégrée)

**Matrice exigences ↔ tests :**
- Pour chaque exigence (hors dossiers) : nombre de tests associés + liste
- Mise en évidence des exigences non couvertes (test_count = 0)
- Exports CSV et PDF (WeasyPrint, orientation paysage A4)

---

#### 2.2.9 Notifications email — `apps.notifications`

**Déclenchement :**
- Signal `post_save` sur `TicketLog`
- Appelle `notify_ticket_created(ticket)` si premier log (from_status vide)
- Appelle `notify_ticket_status_changed(log)` pour les changements de statut

**Envoi :**
- Destinataires : assigné + créateur du ticket (si email renseigné)
- Templates HTML : `ticket_created.html`, `ticket_status_changed.html`
- `DEFAULT_FROM_EMAIL` configurable via settings
- `SITE_URL` pour générer les liens absolus dans les emails

**Configuration dev :** `EMAIL_BACKEND = 'console.EmailBackend'`

---

#### 2.2.10 Sauvegarde / Restauration — `apps.backup`

**Vues :**
| URL | Nom | Description |
|-----|-----|-------------|
| `/admin/backup/` | `admin_backup` | Télécharger archive ZIP |
| `/admin/restore/` | `admin_restore` | Restaurer depuis ZIP |

**Sauvegarde :**
- `dumpdata` (exclut contenttypes, auth.Permission) → `db.json`
- Ajout de `version.txt` avec timestamp
- Ajout de tous les fichiers dans `media/` (structure préservée)
- Compression ZIP → téléchargement

**Restauration :**
- Validation : présence de `version.txt` et `db.json`
- `flush` (interactive=False) → vide la base
- `loaddata` → restaure les données
- Extraction des fichiers médias dans `media/`
- Messages flash de succès/erreur
- Bouton dans l'admin index (`/admin/`) uniquement pour les `staff_member`

---

### 2.3. Interface utilisateur

#### 2.3.1 Template de base (`base.html`)
- Navbar : logo "Cyonima ALM", lien Projets, Utilisateurs (admin), nom utilisateur, mot de passe, déconnexion
- Messages flash (vert succès, rouge erreur)
- Content block

#### 2.3.2 Template projet (`projects/base_project.html`)
- Étend `base.html`
- Sidebar gauche (8 entrées) + content block

#### 2.3.3 Sidebar (`projects/_sidebar.html`)
- 8 liens : Tableau de bord, Membres, Exigences, Tests, Campagnes, Tickets, Traçabilité, Journal, Rapport temps
- Mise en évidence de l'entrée active via `request.resolver_match.url_name`
- Fond blanc, coins arrondis, shadow

### 3.4 Design system
- Tailwind CSS via CDN
- Couleurs : indigo (primaire), gris (neutre), rouge (erreur/incident), vert (succès/validation), bleu (tâche), violet (fait technique)
- Boutons : fond indigo, hover indigo plus foncé

---

### 2.4. Règles de gestion transverses

#### 2.4.1 Contrôle d'accès
- Toutes les vues (sauf login) décorées avec `@login_required`
- Vues dans un projet : `project.user_can_access(request.user)` → redirection avec message flash si refusé
- `is_admin=True` : accès à tous les projets sans être membre
- Admin Django : `is_staff=True`

#### 2.4.2 Messages flash
- Succès : vert (`messages.success`)
- Erreur : rouge (`messages.error`)
- Affichés en haut de page dans `base.html`

#### 2.4.3 Pièces jointes
- Limitées à un fichier par upload (FileField, pas Multiple)
- Chemin de stockage : `<app>/<project_id>/<parent_id>/<filename>`
- `filename` enregistré automatiquement à la création
- Suppression physique du fichier + suppression en base

#### 2.4.4 Numérotation
- Exigences : `0001` par projet (incrément max + 1)
- Tests : `0001` par projet
- Tickets : `XXX-0001` par projet+type (INC/TCH/FT)
- Dossiers : `D-0001` (même compteur que les exigences)

---

### 3/ Security Blog:

Cette section est accessible à tous les utilisateurs enregistrés, mais seul les utilisateurs disposant du profil "officier de sécurité" peuvent écrire des articles dedans. Les articles sont composés d'un ID "Secu-yyyy-xxxx" ou "yyyy" représente l'année de publication et "xxxx" est un entier auto incrémental partant de "0001", d'un titre (Texte court moins de 255 caractères) et d'un champs contenu (Texte long si possible jusqu'à 10000 caractères). Les articles peuvent aussi intégrer des pièces jointes de type PDF (optionel).

Les articles doivent pouvoir être exportés au formt PDF.

### 4/ Blog de la direction:

Cette section est accessible à tous les utilisateurs enregistrés, mais seul les utilisateurs disposant du profil "direction générale" peuvent écrire des articles dedans. Les articles sont composés d'un ID "DG-yyyy-xxxx" ou "yyyy" représente l'année de publication et "xxxx" est un entier auto incrémental partant de "0001", d'un titre (Texte court moins de 255 caractères) et d'un champs contenu (Texte long si possible jusqu'à 10000 caractères). Les articles peuvent aussi intégrer des pièces jointes de type PDF (optionel).

Les articles doivent pouvoir être exportés au formt PDF.

### 5/ Blog de la communication:

Cette section est accessible à tous les utilisateurs enregistrés, mais seul les utilisateurs disposant du profil "communication" peuvent écrire des articles dedans. Les articles sont composés d'un ID "COM-yyyy-xxxx" ou "yyyy" représente l'année de publication et "xxxx" est un entier auto incrémental partant de "0001", d'un titre (Texte court moins de 255 caractères) et d'un champs contenu (Texte long si possible jusqu'à 10000 caractères). Les articles peuvent aussi intégrer des pièces jointes de type PDF (optionel).

Les articles doivent pouvoir être exportés au formt PDF.

### 6/ Blog de l'IT:

Cette section est accessible à tous les utilisateurs enregistrés, mais seul les utilisateurs disposant du profil "direction générale" peuvent écrire des articles dedans. Les articles sont composés d'un ID "DG-yyyy-xxxx" ou "yyyy" représente l'année de publication et "xxxx" est un entier auto incrémental partant de "0001", d'un titre (Texte court moins de 255 caractères) et d'un champs contenu (Texte long si possible jusqu'à 10000 caractères). Les articles peuvent aussi intégrer des pièces jointes de type PDF (optionel).

Les articles doivent pouvoir être exportés au formt PDF.

### 7/ Zone d'échange du Comex:

Cette section est accessible uniquement aux utilisateurs enregistrés disposant du profil "direction générale" qui peuvent écrire des messages dedans. Les articles sont composés d'un ID "COMEX-yyyy-xxxx" ou "yyyy" représente l'année de publication et "xxxx" est un entier auto incrémental partant de "0001" et d'un champs contenu (Texte long si possible jusqu'à 4000 caractères). Les articles peuvent aussi intégrer des pièces jointes de type PDF (optionel). C'est une sorte de forum pour les membres de la direction. Les messages doivent indiquer par qui ils ont été posté.

Un membre du comex peut ainsi créer un fil de discussion avec un titre, les différents membres du COMEX échangeant dedans de manière privée. Le nombre de fils de discussion n'étant pas limité.


## exigences globales de l'application :

- Une option de sauvegarde / restauration de l'ensemble des données depuis le panel d'administration
- Gestion des profils utilisateurs depuis l'interface d'administration
- Activation d'un système de notifications des utilisateurs par mail
- Possibilité de mettre une authentification double facteur par mail
- L'accès aux différentes sous applications se fait via la page d'accueil via un système de tuiles si possible avec des images ajoutée dans la tuile pour rendre l'application plus aggréables visuellement
- Des images pour améliorer le look du site sont disponible dans le répertoire images (je les ai nommées de manière identifiables afin de faciliter leur affectation aux tuiles et au logo global de l'application)
- L'idée est d'avoir une application fonctionnelle, intuitive, mais graphiquement jolie
- possibilité de configuration de l'authentification via un AD Microsoft ou via OpenLDAP avec les protocol adaptés

## exigences documentaires
- un readme assez complet
- un fichier manuel.md qui détaille comment utiliser l'application
- un fichier install.md qui explique comment installer l'application

## Tests
- un maximum de tests unitaires
- un venv de test en port 8080 pour tester l'application générée