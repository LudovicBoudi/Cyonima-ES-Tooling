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

### Web Analytics
- `/administration/analytiques/` — tableau de bord des visites :
  - Vues totales et visiteurs uniques (7 et 30 jours)
  - Graphique d'évolution quotidienne (Chart.js)
  - Pages les plus visitées
- Les visites sont enregistrées automatiquement via un middleware (hors pages d'administration et statiques).

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

## 8. CRM — Gestion de la Relation Client (`/crm/`)

Module de gestion commerciale avec pipeline de ventes.

### Fonctionnalités
- **Tableau de bord** : compteurs (sociétés, contacts, affaires), pipeline, montants gagnés/perdus (Chart.js), interactions récentes, tâches à venir et en retard.
- **Sociétés** : fiche complète (coordonnées, SIRET, secteur), liste avec nombre de contacts et d'affaires, détail avec contacts et affaires liés.
- **Contacts** : prénom, nom, société, fonction, coordonnées, notes.
- **Affaires** : pipeline avec étapes (Prospection → Devis → Négociation → Gagné / Perdu), montant, probabilité, date de clôture prévue.
- **Interactions** : historique des appels, emails, réunions et notes liés à un contact/affaire. Filtrable par contact ou affaire.
- **Tâches** : todo liées à un contact ou une affaire, avec assignation, échéance, marquage terminé/à faire.

---

## 9. RH — Ressources Humaines (`/rh/`)

Gestion administrative du personnel.

### Fonctionnalités
- **Tableau de bord** : effectif, actifs, essais, congés en cours, demandes en attente, graphiques (employés par département, contrats par type), anniversaires du mois, dernières demandes de congé.
- **Employés** : fiche complète (coordonnées, département, poste, société prestataire, statut, date d'embauche, contact d'urgence, notes). Consultation des contrats et congés liés.
- **Départements** : liste avec nombre d'employés, description.
- **Contrats** : CDI, CDD, mission, stage, alternance, freelance, intérim — avec dates, salaire, poste. Colorisation par échéance (vert >3mo, jaune 1-3mo, orange <1mo, rouge expiré/semaine). CDI toujours vert.
- **Congés** : demandes avec workflow de validation (demandé → validé / refusé). Types : CP, RTT, maladie, maternité, sans solde, formation. Affichage du nombre de jours. Calendrier mensuel avec navigation, affichage par initiales colorées. Détection de conflits (chevauchement dans le même département).

---

## 10. ERP — Devis et Factures (`/erp/`)

Module de gestion comptable avec devis, factures, avoirs et paiements.

### Identifiants
| Document | Préfixe | Exemple |
|----------|---------|---------|
| Devis | `DEV-{seq:04d}` | `DEV-0042` |
| Facture | `FACT-{seq:04d}` | `FACT-0018` |
| Avoir | `AVOIR-{seq:04d}` | `AVOIR-0003` |
| Facture fournisseur | `FACF-{seq:04d}` | `FACF-0007` |

### Fonctionnalités
- **Tableau de bord** : CA mensuel et trimestriel, impayés, donut par statut.
- **Devis → Facture** : conversion en un clic depuis le détail du devis.
- **Lignes** : chaque document contient des lignes (description, quantité, prix unitaire, TVA) stockées en JSON.
- **Paiements** : création d'un paiement qui met automatiquement la facture en statut « payée » si le montant est atteint.
- **Avoirs** : documents de correction liés à une facture.
- **Factures fournisseurs** : suivi des factures reçues.

---

## 11. GED — Gestion Électronique de Documents (`/ged/`)

Module de classement, recherche et téléchargement de fichiers avec catégories et tags.

### Fonctionnalités
- **Catégories** : catégories colorées pour organiser les documents.
- **Recherche** : champ de recherche plein texte avec filtre par catégorie.
- **Prévisualisation** : aperçu des images et des PDF directement dans le navigateur.
- **Téléchargement** : compteur de téléchargements automatique.
- **Numérotation** : chaque document reçoit un numéro de registre `DOC-{année}-{seq:05d}`.
- **Tags** : tags libres pour un classement transversal.
- **Versioning** : champ version pour le suivi des révisions.

---

## 12. Ressources Externes (`/ressources/`)

Pages d'information statiques sur les principales réglementations SSI.

### Pages disponibles
| Ressource | Description |
|-----------|-------------|
| **RGPD** | Règlement Général sur la Protection des Données (UE) 2016/679 |
| **IGI 1300** | Instruction Générale Interministérielle — protection du secret de la défense nationale |
| **IM 900** | Instruction Ministérielle — protection du secret au ministère des Armées |
| **II 901** | Instruction Interministérielle — protection des SI diffusion restreinte |
| **PCI DSS** | Payment Card Industry Data Security Standard (v4.0) |
| **NIS 2** | Directive européenne sur la sécurité des réseaux et des systèmes d'information |
| **EBIOS RM** | Méthode française d'analyse des risques SSI (ANSSI) |
| **IEC 62443** | Cybersécurité des systèmes industriels et ICS |
| **ISO 27001** | Management de la sécurité de l'information (SMSI) |
| **ISO 27032** | Lignes directrices pour la cybersécurité |

### Navigation
- Page d'accueil : grille de toutes les ressources disponibles.
- Chaque page contient un sommaire avec ancres, un bandeau coloré, et des sections détaillées.
- Retour facile à la liste via le lien en bas de page.

---

## 13. COMEX (`/comex/`)

Forum d'échange réservé à la direction et aux administrateurs.
- Création de fils de discussion.
- Réponses dans les fils.
- Accès : rôle `direction` ou `admin`.

---

## 14. Notifications

- **Paramètres** : chaque utilisateur peut configurer ses notifications par type (email ou in-app) via son profil.
- Création automatique d'un paramétrage vide à la création du compte.
- Déclenchement : manuel via `Notification.objects.create()` dans le code.

---

## 15. Rôles et permissions

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

## 16. Double authentification (2FA)

1. L'utilisateur active la 2FA dans son profil.
2. À la connexion, un code à 6 chiffres est envoyé par email.
3. Le code est valable 5 minutes.
4. Saisie du code sur la page de vérification avant accès à l'application.
