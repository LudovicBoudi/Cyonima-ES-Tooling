# Documentation utilisateur — Cyonima-ES-Tools

## 1. Authentification

### Connexion
- Page de connexion : `/accounts/login/`
- La double authentification par email (2FA) peut être activée dans le profil utilisateur.

### Déconnexion
- accessible via le menu utilisateur en haut à droite.

---

## 2. Administration (`/administration/`)

Réservé aux membres du staff (`is_staff=True`).

### Utilisateurs
- **Liste** : `/administration/utilisateurs/` — tableau avec rôles multiples.
- **Création** : formulaire avec nom, email, mot de passe, sélection des rôles.
- **Modification** : éditer le profil, activer/désactiver, changer les rôles.
- **Suppression** : confirmation avant suppression.

### Configuration
- **Nom du site** : modifiable depuis `/administration/configuration/`.
- **Logo** : téléversement d'un fichier image.

### Sauvegarde
- `/administration/sauvegarde/` — génère une archive ZIP contenant :
  - Export JSON complet de la base (`dumpdata`)
  - Fichiers médias
  - Fichier `version.txt` avec la date

---

## 3. Budget IT (`/budget/`)

### Tableau de bord (`/budget/dashboard/`)
- Graphiques Chart.js :
  - Donut : répartition par type de DAT
  - Barres : montants par type budgétaire
  - Courbe d'évolution : consommation mensuelle et budget restant
- Alertes budgétaires : seuils à 80 % (orange) et 100 % (rouge)

### DAT — Demandes d'Achat Travaux (`/budget/dat/`)
Les DAT sont identifiées par `IT-XXXX-ANNEE`.

#### Workflow des statuts
1. **Brouillon** : création, modification possible
2. **Soumise** : envoyée pour validation (bouton "Soumettre")
3. **Validée** : approuvée (bouton "Valider")
4. **Rejetée** : refusée (bouton "Rejeter")

#### Fonctionnalités
- Création avec produits multiples (ajout dynamique de lignes)
- Édition, duplication, suppression
- Export CSV, XLSX (openpyxl), PDF (WeasyPrint)
- Affichage détaillé avec lignes de produits

### Budgets annuels (`/budget/budgets/`)
- CRUD complet : créer, modifier, supprimer des enveloppes budgétaires par année et type.
- Types : Investissement, Fonctionnement.
- Contrôle d'unicité : impossible de créer deux budgets de même type pour la même année.

### Tâches / Todo (`/budget/taches/`)
- Kanban avec 3 colonnes : À faire, En cours, Terminé.
- Glisser-déposer (drag & drop) via fetch pour changer le statut.
- Couleurs selon l'échéance :
  - Vert : > 7 jours
  - Jaune : 3-7 jours
  - Orange : 1-3 jours
  - Rouge : aujourd'hui ou dépassé
- Création rapide, suppression.

### Fournisseurs (`/budget/fournisseurs/`)
- CRUD complet : entreprise, contact, téléphone, email, description.

---

## 4. Guichet IT (`/guichet/`)

Portail de tickets d'incidents et d'expressions de besoins (EBI).

### Types de tickets
| Type | Préfixe | Workflow |
|------|---------|----------|
| **Incident** | `INC-XXXX` | nouveau → en_cours → resolu → ferme |
| **EBI** | `EBI-XXXX` | nouveau → en_etude → valide → realise → ferme |

### Fonctionnalités
- **Liste** : filtre par type (Incidents / EBI) avec onglets.
- **Création** : formulaire avec type, titre, description, assignation.
- **Détail** : affichage complet, historique des transitions, formulaire de transition.
- **Transitions** : changement de statut avec commentaire optionnel, journalisé dans l'historique.

---

## 5. ALM — Gestion de projet (`/projects/`)

### Projets
- CRUD de projets.
- Membres avec rôles : Chef de projet, Développeur, Testeur, Intégrateur.
- Accès restreint aux membres + administrateurs.

### Tickets
3 types avec leurs workflows :

| Type | Préfixe | Workflow |
|------|---------|----------|
| **Incident** | `INC-XXXX` | nouveau → assigne → en_cours → cloture |
| **Tâche** | `TCH-XXXX` | nouveau → assigne → en_cours → valide → cloture |
| **FT** | `FT-XXXX` | nouveau → assigne → en_cours → valide → a_clore → cloture |

Vues disponibles :
- **Liste** : filtrage par type.
- **Kanban** : colonnes par statut.
- **Gantt** : timeline avec dates de début/échéance.
- **Détail** : transitions avec suivi du temps (heures passées) et commentaires.
- **Export CSV** : tous les tickets du projet.

### Exigences / Tests
- Exigences rattachées aux projets.
- Scénarios de test et campagnes de test.
- Traçabilité entre exigences et tests.

### Journal / Rapports
- Journal d'activité.
- Rapport de temps : heures passées par utilisateur et type de ticket.

---

## 6. Blogs (`/blog/*/`)

Quatre blogs accessibles selon le rôle :

| Blog | URL | Rôle requis |
|------|-----|-------------|
| Sécurité | `/blog/securite/` | `securite` ou `admin` |
| Direction | `/blog/direction/` | `direction` ou `admin` |
| Communication | `/blog/communication/` | `communication` ou `admin` |
| IT | `/blog/it/` | `it_manager` ou `admin` |

### Liste des articles
- Affichage complet des articles (titre, image à la une, contenu, métadonnées) les uns en dessous des autres.
- Barre latérale : 30 derniers articles, lien "Tous les articles", bouton "Nouvel article".

### Édition d'articles
- Création et modification avec éditeur de texte riche (CKEditor 5) — mise en forme HTML (titres, gras, listes, etc.).
- Possibilité d'ajouter une image à la une.
- Suppression avec confirmation.

---

## 7. Wiki (`/wiki/`)

Documentation collaborative accessible à tous les utilisateurs connectés.

### Fonctionnalités
- **Liste** des pages avec lien vers le détail.
- **Création** : titre et contenu saisis avec CKEditor 5 (éditeur WYSIWYG).
- **Modification** : toute page peut être éditée (bouton "Modifier").
- **Suppression** : confirmation avant suppression.
- **Slugs** : génération automatique à partir du titre avec gestion des doublons.

---

## 8. COMEX (`/comex/`)

Forum d'échange réservé à la direction et aux administrateurs.
- Création de fils de discussion.
- Réponses dans les fils.
- Accès : rôle `direction` ou `admin`.

---

## 8. Notifications

- **Paramètres** : chaque utilisateur peut configurer ses notifications par type (email ou in-app) via son profil.
- Création automatique d'un paramétrage vide à la création du compte.
- Déclenchement : manuel via `Notification.objects.create()` dans le code.

---

## 9. Rôles et permissions

| Code rôle | Accès |
|-----------|-------|
| `admin` | Tout — accès administration, tous blogs, COMEX, projets |
| `it_manager` | Budget IT, Guichet IT, blog IT |
| `direction` | Blog direction, COMEX |
| `securite` | Blog sécurité |
| `communication` | Blog communication |
| `chef_projet` | Projets ALM |
| `user` | Accès de base (projets assignés, tickets) |

Un utilisateur peut avoir **plusieurs rôles simultanément**.

---

## 10. Double authentification (2FA)

1. L'utilisateur active la 2FA dans son profil.
2. À la connexion, un code à 6 chiffres est envoyé par email.
3. Le code est valable 5 minutes.
4. Saisie du code sur la page de vérification avant accès à l'application.
