# Guide de Déploiement

## Table des matières

1. [Prérequis](#prérequis)
2. [Installation locale](#installation-locale)
3. [Déploiement avec Docker](#déploiement-avec-docker)
4. [Configuration de production](#configuration-de-production)
5. [Mise à jour](#mise-à-jour)
6. [Sauvegarde et restauration](#sauvegarde-et-restauration)
7. [Monitoring](#monitoring)
8. [Dépannage](#dépannage)

## Prérequis

### Pour l'installation locale
- Python 3.11 ou supérieur
- pip (gestionnaire de paquets Python)
- SQLite (développement) ou PostgreSQL/MySQL (production)
- Redis (optionnel, pour les tâches en arrière-plan)

### Pour le déploiement Docker
- Docker 20.10 ou supérieur
- Docker Compose 2.0 ou supérieur

## Installation locale

### 1. Cloner le repository

```bash
git clone <repository-url>
cd Gestions-Marché
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
# Sur Windows
venv\Scripts\activate
# Sur Linux/Mac
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer l'environnement

```bash
cp .env.example .env
# Éditer .env avec vos configurations
```

Variables d'environnement importantes:
- `DATABASE_URL`: URL de la base de données
- `SECRET_KEY`: Clé secrète pour les tokens JWT
- `DEBUG`: Mode debug (True/False)
- `REDIS_URL`: URL du serveur Redis

### 5. Initialiser la base de données

```bash
# Option 1: Avec le script d'initialisation
python init_db.py

# Option 2: Avec Alembic
alembic upgrade head
```

### 6. Peupler la base de données (optionnel)

```bash
python seed_data.py
```

Cela créera des utilisateurs de test et des marchés exemples.

### 7. Lancer l'application

```bash
python run.py
```

L'application sera accessible sur http://localhost:8000

### 8. Accéder à l'application

- Interface web: http://localhost:8000
- Documentation API: http://localhost:8000/docs
- Documentation alternative: http://localhost:8000/redoc

## Déploiement avec Docker

### 1. Construire les images Docker

```bash
docker-compose build
```

### 2. Lancer tous les services

```bash
docker-compose up -d
```

Cela lancera:
- L'application FastAPI (port 8000)
- PostgreSQL (port 5432)
- Redis (port 6379)
- Worker Celery
- Celery Beat (planificateur)
- Nginx (reverse proxy)

### 3. Vérifier les logs

```bash
# Logs de l'application
docker-compose logs -f app

# Logs de tous les services
docker-compose logs -f
```

### 4. Arrêter les services

```bash
docker-compose down
```

### 5. Redémarrer un service spécifique

```bash
docker-compose restart app
```

## Configuration de production

### 1. Base de données PostgreSQL

Pour la production, utilisez PostgreSQL au lieu de SQLite:

```bash
# Dans .env
DATABASE_URL=postgresql://user:password@localhost:5432/gestion_marches
```

### 2. Configuration Nginx

Créez un fichier `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /static {
            alias /app/app/static;
        }

        location /uploads {
            alias /app/uploads;
        }
    }
}
```

### 3. Configuration SSL/TLS

Pour HTTPS, utilisez Let's Encrypt ou des certificats personnalisés:

```bash
# Installer certbot
apt-get install certbot python3-certbot-nginx

# Obtenir un certificat
certbot --nginx -d your-domain.com
```

### 4. Variables d'environnement de production

```bash
# .env.production
DATABASE_URL=postgresql://user:password@db:5432/gestion_marches
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<votre-clé-secrète-forte>
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

## Mise à jour

### Mise à jour locale

```bash
# 1. Sauvegarder la base de données
python backup_database.py

# 2. Mettre à jour le code
git pull

# 3. Mettre à jour les dépendances
pip install -r requirements.txt --upgrade

# 4. Appliquer les migrations
alembic upgrade head

# 5. Redémarrer l'application
```

### Mise à jour Docker

```bash
# 1. Sauvegarder les données
docker-compose exec db pg_dump -U postgres gestion_marches > backup.sql

# 2. Mettre à jour le code
git pull

# 3. Reconstruire les images
docker-compose build

# 4. Redémarrer les services
docker-compose up -d
```

## Sauvegarde et restauration

### Sauvegarde automatique

L'application effectue des sauvegardes automatiques quotidiennes dans le répertoire `backups/`.

### Sauvegarde manuelle

```bash
# SQLite
cp marches_publics.db backups/backup_$(date +%Y%m%d_%H%M%S).db

# PostgreSQL
docker-compose exec db pg_dump -U postgres gestion_marches > backup.sql
```

### Restauration

```bash
# SQLite
cp backups/backup_20240101_120000.db marches_publics.db

# PostgreSQL
docker-compose exec -T db psql -U postgres gestion_marches < backup.sql
```

## Monitoring

### Logs

Les logs sont stockés dans le répertoire `logs/`:
- `app.log`: Logs de l'application
- `celery.log`: Logs des tâches Celery
- `error.log`: Logs d'erreurs

### Monitoring avec Prometheus (optionnel)

Ajoutez Prometheus pour le monitoring:

```yaml
# docker-compose.yml
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

### Monitoring avec Grafana (optionnel)

```yaml
# docker-compose.yml
grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
  volumes:
    - grafana_data:/var/lib/grafana
```

## Dépannage

### L'application ne démarre pas

1. Vérifier les logs: `docker-compose logs app`
2. Vérifier que la base de données est accessible
3. Vérifier les variables d'environnement
4. Vérifier les ports disponibles

### Erreur de connexion à la base de données

1. Vérifier que PostgreSQL est en cours d'exécution
2. Vérifier les identifiants dans `.env`
3. Vérifier que la base de données existe

### Les tâches Celery ne s'exécutent pas

1. Vérifier que Redis est en cours d'exécution
2. Vérifier les logs du worker: `docker-compose logs celery_worker`
3. Vérifier la configuration dans `app/tasks/celery_app.py`

### Erreur de mémoire

1. Augmenter la mémoire allouée à Docker
2. Optimiser les requêtes de base de données
3. Utiliser la pagination pour les grandes listes

### Problèmes de performance

1. Activer le cache Redis
2. Optimiser les index de base de données
3. Utiliser des workers supplémentaires
4. Activer la compression des réponses

## Sécurité

### Recommandations de sécurité

1. **Changez la clé secrète** par défaut en production
2. **Utilisez HTTPS** en production
3. **Limitez les tentatives de connexion** (rate limiting)
4. **Activez les logs de sécurité**
5. **Effectuez des sauvegardes régulières**
6. **Tenez les dépendances à jour**
7. **Utilisez des variables d'environnement** pour les secrets
8. **Activez le CORS** uniquement pour les domaines autorisés

### Firewall

Configurez le firewall pour n'autoriser que les ports nécessaires:
- 80 (HTTP)
- 443 (HTTPS)
- 22 (SSH, si nécessaire)

## Support

Pour toute question ou problème, consultez:
- La documentation API: http://localhost:8000/docs
- Les logs dans le répertoire `logs/`
- Le fichier README.md pour l'utilisation de l'application
