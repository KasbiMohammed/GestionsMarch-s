# Gestion des Marchés Publics - Application Web pour Communes Territoriales Marocaines

Application web moderne, professionnelle et sécurisée pour la gestion, le suivi et le contrôle de toutes les étapes des marchés publics des communes territoriales marocaines.

## Technologies Utilisées

### Backend
- **FastAPI** - Framework web moderne et performant
- **SQLAlchemy** - ORM pour la gestion de la base de données
- **SQLite** - Base de données pour le développement (PostgreSQL/MySQL en production)
- **Alembic** - Gestion des migrations de base de données

### Frontend
- **Jinja2** - Moteur de templates HTML
- **Bootstrap 5** - Framework CSS responsive
- **HTML5, CSS3, JavaScript** - Technologies web standards
- **Plotly/Chart.js** - Graphiques et tableaux de bord interactifs

### Traitement de Données
- **Pandas** - Manipulation et analyse de données
- **NumPy** - Calculs scientifiques
- **Requests/BeautifulSoup4/lxml** - Scraping du portail PMMP

### Exports & Rapports
- **OpenPyXL** - Export Excel
- **ReportLab** - Génération de rapports PDF
- **pdfplumber** - Traitement de documents PDF

### Autres
- **Passlib** - Hachage des mots de passe
- **Python-JOSE** - Gestion des tokens JWT
- **Celery/Redis** - Tâches en arrière-plan
- **Loguru** - Système de logging

## Architecture du Projet

```
gestion-marches/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application FastAPI principale
│   ├── config.py               # Configuration de l'application
│   ├── database.py             # Configuration de la base de données
│   │
│   ├── models/                 # Modèles SQLAlchemy
│   │   ├── __init__.py
│   │   ├── user.py            # Utilisateurs et rôles
│   │   ├── market.py          # Marchés publics
│   │   ├── stage.py           # Étapes des marchés
│   │   ├── document.py        # Documents et pièces jointes
│   │   └── history.py         # Historique des modifications
│   │
│   ├── schemas/                # Schémas Pydantic
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── market.py
│   │   ├── stage.py
│   │   └── document.py
│   │
│   ├── api/                    # Routes API
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentification
│   │   ├── users.py           # Gestion des utilisateurs
│   │   ├── markets.py         # Gestion des marchés
│   │   ├── stages.py          # Gestion des étapes
│   │   ├── documents.py       # Gestion des documents
│   │   ├── dashboard.py       # Tableau de bord
│   │   ├── search.py          # Recherche avancée
│   │   └── exports.py         # Exports
│   │
│   ├── services/               # Logique métier
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── market_service.py
│   │   ├── stage_service.py
│   │   ├── notification_service.py
│   │   └── export_service.py
│   │
│   ├── scraping/               # Scraping PMMP
│   │   ├── __init__.py
│   │   ├── pmmp_scraper.py
│   │   └── market_analyzer.py
│   │
│   ├── utils/                  # Utilitaires
│   │   ├── __init__.py
│   │   ├── security.py
│   │   ├── validators.py
│   │   ├── date_utils.py
│   │   └── file_utils.py
│   │
│   ├── exports/                # Fonctions d'export
│   │   ├── __init__.py
│   │   ├── excel_export.py
│   │   ├── pdf_export.py
│   │   └── word_export.py
│   │
│   ├── dashboard/              # Logique du tableau de bord
│   │   ├── __init__.py
│   │   ├── statistics.py
│   │   ├── charts.py
│   │   └── kpis.py
│   │
│   ├── auth/                   # Authentification
│   │   ├── __init__.py
│   │   ├── dependencies.py
│   │   └── permissions.py
│   │
│   ├── templates/              # Templates Jinja2
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── markets/
│   │   ├── stages/
│   │   └── auth/
│   │
│   └── static/                 # Fichiers statiques
│       ├── css/
│       ├── js/
│       └── img/
│
├── alembic/                    # Migrations Alembic
├── uploads/                    # Fichiers uploadés
├── backups/                    # Sauvegardes de la base de données
├── logs/                       # Logs de l'application
├── tests/                      # Tests unitaires
├── requirements.txt            # Dépendances Python
├── .env.example               # Exemple de fichier d'environnement
├── alembic.ini                 # Configuration Alembic
└── README.md                   # Ce fichier
```

## Installation

1. Cloner le repository
2. Créer un environnement virtuel:
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. Installer les dépendances:
```bash
pip install -r requirements.txt
```

4. Configurer l'environnement:
```bash
cp .env.example .env
# Éditer .env avec vos configurations
```

5. Initialiser la base de données:
```bash
alembic upgrade head
```

6. Lancer l'application:
```bash
uvicorn app.main:app --reload
```

L'application sera accessible sur http://localhost:8000

## Fonctionnalités Principales

### Gestion des Marchés
- Création et modification de marchés publics
- Fiche complète avec toutes les informations
- Suivi de toutes les étapes administratives et techniques
- Gestion des documents et pièces jointes
- Calcul automatique des retards et alertes

### Gestion des Étapes
- Check-list interactive pour chaque étape
- Suivi de l'état d'avancement en pourcentage
- Statuts: Non commencé, En cours, Terminé, En attente, Bloqué, Annulé
- Dates prévues et réelles
- Responsables et observations
- Historique des modifications

### Analyse Automatique PMMP
- Scraping automatique du portail des marchés publics
- Extraction des montants des offres
- Calcul du prix de référence (médiane, moyenne, moyenne tronquée, IQR)
- Détection automatique des offres anormalement basses/élevées
- Génération de rapports avec graphiques et recommandations

### Tableau de Bord
- KPIs en temps réel
- Graphiques interactifs (Plotly/Chart.js)
- Statistiques sur les marchés
- Alertes visuelles (vert, orange, rouge)
- Notifications automatiques

### Gestion des Utilisateurs
- Rôles: Administrateur, Président, Directeur des Services, Service des Marchés, Service Technique, Service Financier, Contrôle Interne, Consultation
- Droits d'accès spécifiques par rôle
- Authentification JWT sécurisée

### Recherche Avancée
- Recherche par numéro, objet, entreprise, année, budget, statut
- Filtrage multi-critères
- Résultats en temps réel

### Exports
- Export Excel (OpenPyXL)
- Export PDF (ReportLab)
- Export Word
- Rapports automatiques

### Autres Fonctionnalités
- Sauvegarde automatique de la base de données
- Système de logging complet
- Historique des modifications
- Interface responsive et moderne
- Conforme à la réglementation marocaine

## Rôles et Permissions

### Administrateur
- Accès complet à toutes les fonctionnalités
- Gestion des utilisateurs et des rôles
- Configuration du système

### Président de la Commune
- Validation des marchés
- Consultation de tous les marchés
- Rapports et statistiques

### Directeur des Services
- Gestion des marchés
- Validation des étapes
- Rapports et statistiques

### Service des Marchés
- Gestion complète des marchés
- Suivi des étapes
- Gestion des documents

### Service Technique
- Validation technique
- Suivi des travaux
- Attachements et décomptes

### Service Financier
- Validation financière
- Engagement comptable
- Gestion des paiements

### Contrôle Interne
- Audit et contrôle
- Consultation et rapports
- Vérification de conformité

### Consultation
- Lecture seule
- Consultation des marchés
- Export des rapports

## Développement

### Structure Modulaire
Le projet est organisé en modules indépendants pour faciliter la maintenance et l'évolution:
- **API**: Endpoints REST
- **Models**: Schéma de base de données
- **Services**: Logique métier
- **Scraping**: Intégration PMMP
- **Exports**: Génération de documents
- **Dashboard**: Statistiques et KPIs
- **Auth**: Sécurité et permissions

### Bonnes Pratiques
- Code documenté avec docstrings
- Type hints Python
- Tests unitaires
- Logging complet
- Gestion d'erreurs robuste
- Validation des données

## Licence

Ce projet est développé pour les communes territoriales marocaines.

## Support

Pour toute question ou problème, veuillez contacter l'équipe de développement.
