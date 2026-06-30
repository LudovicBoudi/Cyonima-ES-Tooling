# Cyonima-ES-Tools

Plateforme web modulaire pour la gestion IT, le suivi de projet ALM, la communication interne et le helpdesk en Français proposé par Cyonima de la communauté RENEGA2.

## Modules

| Module | Description | Accès |
|--------|-------------|-------|
| **Administration** | Gestion des utilisateurs, rôles, configuration, sauvegarde | `/administration/` |
| **Budget IT** | Budgets annuels, DAT, fournisseurs, tâches, tableau de bord | `/budget/` |
| **Guichet IT** | Tickets d'incidents et expressions de besoins informatiques | `/guichet/` |
| **ALM** | Projets, exigences, tests, tickets (incidents/tâches/FT) | `/projects/` |
| **Blogs** | Sécurité, direction, communication, IT | `/blog/*/` |
| **Wiki** | Pages de documentation collaborative | `/wiki/` |
| **COMEX** | Forum d'échange du comité exécutif | `/comex/` |

## Prérequis

- Python 3.12+
- pip (ou venv)

## Installation rapide

```bash
# 1. Cloner le dépôt
git clone <url> && cd Cyonima-ES-Tooling

# 2. Environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 3. Dépendances
pip install -r requirements.txt

# 4. Configuration
cp .env .env  # déjà présent, adapter si besoin
# Variables : SECRET_KEY, DEBUG, ALLOWED_HOSTS, EMAIL_BACKEND, DEFAULT_FROM_EMAIL, SITE_URL

# 5. Base de données
python manage.py migrate

# 6. Compte admin
python manage.py createsuperuser
# ou charger les données initiales :
python manage.py loaddata apps/accounts/fixtures/initial_roles.json  # si présent

# 7. Lancement
python manage.py runserver 0.0.0.0:8080
```

Serveur accessible sur `http://127.0.0.1:8080`.

## Compte par défaut

- Identifiant : `admin`
- Mot de passe : `admin123Admin!`
- Rôles : `admin` (tous accès), `it_manager` (budget, guichet, blog IT)

## Sauvegarde

```bash
python manage.py cyonima_backup
```

Génère une archive ZIP (dump JSON + médias) dans le répertoire courant.
Accès via l'interface : `/administration/sauvegarde/`.

## Technologies

- Django 6.0.6, Python 3.12
- Tailwind CSS (CDN)
- SQLite (développement), PostgreSQL/MySQL (production)
- Chart.js (graphiques), WeasyPrint (PDF), openpyxl (XLSX)
- CKEditor 5 (éditeur de texte riche) — blogs et wiki
