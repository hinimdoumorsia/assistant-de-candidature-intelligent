# 🎯 SCA Desktop — Système de Candidature Automatique aux Stages

> **Application desktop Python/PyQt6** qui automatise la veille d'offres de stage et la préparation des candidatures, avec IA Claude intégrée.

---

## Table des Matières

1. [Présentation du projet](#1-présentation-du-projet)
2. [Prérequis système](#2-prérequis-système)
3. [Cloner le projet](#3-cloner-le-projet)
4. [Installation des dépendances](#4-installation-des-dépendances)
5. [Configuration des APIs et variables d'environnement](#5-configuration-des-apis-et-variables-denvironnement)
6. [Lancer l'application](#6-lancer-lapplication)
7. [Architecture du projet](#7-architecture-du-projet)
8. [Fonctionnalités détaillées](#8-fonctionnalités-détaillées)
9. [Sécurité — Problèmes et bonnes pratiques](#9-sécurité--problèmes-et-bonnes-pratiques)
10. [Résolution des problèmes fréquents](#10-résolution-des-problèmes-fréquents)
11. [Migration vers la v2 Web](#11-migration-vers-la-v2-web)
12. [Contribuer](#12-contribuer)

---

## 1. Présentation du projet

SCA Desktop est une application **Python/PyQt6** qui automatise :

- **La veille d'offres de stage** sur 6 sources gratuites (Indeed, Rekrute, Emploi.ma, Bayt, Adzuna, Remotive)
- **Le scoring automatique** offre ↔ profil (TF-IDF local + Claude API)
- **La génération de lettres de motivation** multi-variantes via Claude AI
- **Un coach IA** qui analyse votre candidature et identifie vos forces/lacunes
- **Un simulateur d'entretien** en mode chat avec Claude jouant le recruteur
- **Un historique complet** avec statistiques et export PDF

### Palette de couleurs

| Rôle         | Couleur    | Usage                          |
|--------------|------------|-------------------------------|
| Primaire     | `#1DB954`  | Vert — boutons, accents, KPI  |
| Secondaire   | `#0F3D2E`  | Vert foncé — sidebar           |
| Accent       | `#FF6B35`  | Orange — CTA, alertes          |
| Fond         | `#F8FFFE`  | Blanc verdâtre — background    |
| Texte        | `#1A2E22`  | Vert très foncé — texte body   |

---

## 2. Prérequis système

| Outil          | Version minimale | Vérification             |
|----------------|-----------------|--------------------------|
| Python         | 3.11+           | `python --version`       |
| pip            | 23+             | `pip --version`          |
| Git            | 2.x             | `git --version`          |
| OS             | Windows 10/11, macOS 12+, Ubuntu 22.04+ | —     |
| RAM            | 4 Go minimum, 8 Go recommandé | —         |
| Espace disque  | ~500 Mo (avec Playwright) | —            |

> ⚠️ **Python 3.11+ obligatoire** — PyQt6 6.6+ ne supporte pas Python 3.10 ou antérieur.

---

## 3. Cloner le projet

```bash
# 1. Cloner le dépôt
git clone https://github.com/votre-username/sca-desktop.git
cd sca-desktop

# 2. Vérifier la structure
ls -la
# Vous devez voir : main.py, config.py, requirements.txt, .env.example, ...
```

Si vous n'avez pas Git installé :

```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt-get install git

# Windows — Téléchargez depuis https://git-scm.com/download/win
```

---

## 4. Installation des dépendances

### 4.1 Créer un environnement virtuel (fortement recommandé)

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer (Linux/macOS)
source venv/bin/activate

# Activer (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activer (Windows CMD)
venv\Scripts\activate.bat
```

Votre terminal doit afficher `(venv)` au début de chaque ligne.

### 4.2 Installer les packages Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Durée estimée : **2 à 5 minutes** selon votre connexion.

### 4.3 Installer Playwright (navigateur Chromium)

Playwright est utilisé pour le scraping de Rekrute et Emploi.ma :

```bash
# Installer le navigateur Chromium
playwright install chromium

# Si erreur de permissions sur Linux
playwright install --with-deps chromium
```

> 💡 Cette étape télécharge ~150 Mo. Elle n'est nécessaire qu'une seule fois.

### 4.4 Vérifier l'installation

```bash
python -c "import PyQt6; import anthropic; import playwright; print('✅ Toutes les dépendances OK')"
```

---

## 5. Configuration des APIs et variables d'environnement

### 5.1 Créer le fichier `.env`

```bash
# Copier le fichier modèle
cp .env.example .env
```

Ouvrez `.env` avec votre éditeur préféré :

```bash
# Linux/macOS
nano .env
# ou
code .env

# Windows
notepad .env
```

### 5.2 Configurer Claude API (Anthropic)

1. Rendez-vous sur [https://console.anthropic.com](https://console.anthropic.com)
2. Créez un compte ou connectez-vous
3. Dans **API Keys**, cliquez **Create Key**
4. Copiez la clé (elle commence par `sk-ant-`)
5. Collez dans `.env` :

```env
CLAUDE_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxx
CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

> 💰 **Coût estimé** : ~$0.003 par scoring d'offre, ~$0.01 par lettre générée. Un budget de $5 couvre plusieurs semaines d'usage intensif.

### 5.3 Configurer Adzuna API (gratuit)

1. Rendez-vous sur [https://developer.adzuna.com](https://developer.adzuna.com)
2. Cliquez **Register** — inscription gratuite
3. Créez une application dans votre dashboard
4. Récupérez `App ID` et `App Key`
5. Collez dans `.env` :

```env
ADZUNA_APP_ID=a1b2c3d4
ADZUNA_API_KEY=e5f6g7h8i9j0k1l2
```

> ℹ️ Le plan gratuit offre **1 000 requêtes/mois**, largement suffisant pour une utilisation personnelle.

### 5.4 Vérifier votre fichier `.env`

```env
# Exemple de .env correctement configuré
CLAUDE_API_KEY=sk-ant-api03-VotreVraieCle
CLAUDE_MODEL=claude-3-5-sonnet-20241022
ADZUNA_APP_ID=votre_app_id
ADZUNA_API_KEY=votre_app_key
DATABASE_URL=sqlite:///data/sca_data.db
APP_SECRET_KEY=une_longue_chaine_aleatoire_unique
DEBUG=False
LOG_LEVEL=INFO
```

> 🔐 **IMPORTANT** : Ne commitez jamais `.env` sur Git. Il est déjà dans `.gitignore`.

---

## 6. Lancer l'application

```bash
# S'assurer d'être dans le bon dossier et venv activé
cd sca-desktop
source venv/bin/activate  # Linux/macOS

# Lancer l'application
python main.py
```

### Première utilisation

1. **Fenêtre de connexion** → Cliquez **Créer un compte**
2. Remplissez nom, prénom, email, mot de passe (min. 8 caractères)
3. Connectez-vous avec vos identifiants
4. **Dashboard** → Complétez votre profil (onglet "Mon Profil")
5. Cliquez **🔄 Scanner maintenant** pour lancer votre premier scraping

### Lancer en mode debug

```bash
DEBUG=True python main.py
```

### Lancer les tests

```bash
pytest tests/ -v
```

---

## 7. Architecture du projet

```
sca_desktop/
├── main.py                    # Point d'entrée — login → dashboard
├── config.py                  # Configuration centrale + thème Qt
├── requirements.txt           # Dépendances Python
├── .env.example               # Modèle variables d'environnement
├── .gitignore                 # Fichiers à ne jamais committer
│
├── ui/                        # Interface PyQt6 UNIQUEMENT (aucun import service ici)
│   ├── login_window.py        # Connexion / inscription
│   ├── dashboard.py           # Fenêtre principale + sidebar
│   ├── profile_editor.py      # Éditeur de profil + parsing CV
│   ├── notification_popup.py  # Popup offre + QWizard dépôt assisté
│   ├── candidature_history.py # Historique filtrable + export rapport
│   └── interview_simulator.py # Coach IA + simulateur d'entretien chat
│
├── services/                  # Logique métier pure Python (testable sans Qt)
│   ├── auth_service.py        # Inscription, login, bcrypt, session mémoire
│   ├── profile_service.py     # CRUD profils, parsing CV PDF
│   ├── matching_service.py    # TF-IDF + Claude API scoring
│   ├── generator_service.py   # LM, CV, coach, simulateur (Claude API)
│   ├── scraper_service.py     # RSS feedparser + Playwright + Adzuna API
│   └── pdf_service.py         # Export PDF (ReportLab)
│
├── database/
│   ├── models.py              # SQLAlchemy ORM (User, Profil, Offre, Candidature)
│   └── db_manager.py          # Engine + SessionFactory + context manager
│
├── workers/
│   └── scraper_worker.py      # Daemon APScheduler (scraping toutes les 30 min)
│
├── data/                      # Créé automatiquement — sca_data.db
├── exports/                   # Créé automatiquement — PDF générés
└── logs/                      # Créé automatiquement — sca.log
```

### Règle fondamentale d'architecture

> **Aucune logique métier dans les fichiers `ui/`.** Chaque service Python est un module pur sans import Qt, testable indépendamment. Cette séparation stricte permet la migration web v2 sans réécriture du backend.

---

## 8. Fonctionnalités détaillées

### 8.1 Scraping multi-sources

| Source       | Méthode          | Fréquence     | Notes                          |
|-------------|-----------------|--------------|-------------------------------|
| Indeed RSS   | feedparser       | 30 min       | RSS officiel, très stable      |
| Rekrute.com  | Playwright       | 30 min       | Sélecteurs CSS configurables   |
| Emploi.ma    | Playwright       | 30 min       | Sélecteurs CSS configurables   |
| Bayt.com     | RSS + Playwright | 30 min       | RSS principal + détails PW     |
| Adzuna API   | httpx (API REST) | 30 min       | 1000 req/mois gratuit          |
| Remotive RSS | feedparser       | Désactivé    | Activer dans config.py         |

### 8.2 Pipeline de scoring

```
Offre détectée
     │
     ▼
TF-IDF local (scikit-learn)
     │ score < 40% → ignorée
     │ score ≥ 40% ↓
     ▼
Claude API scoring sémantique (0-100)
     │ JSON : score, compétences matchées/manquantes, recommandation
     ▼
Notification si score ≥ seuil configuré
```

### 8.3 Génération IA

- **Lettre de motivation** : 3 variantes (technique / humaine / projet)
- **CV structuré** : JSON → PDF ReportLab
- **Coach** : points forts, lacunes, mots-clés manquants, conseils
- **Simulateur entretien** : chat multi-tours, Claude joue le recruteur

### 8.4 Dépôt assisté (QWizard 3 étapes)

1. Choisir la variante de lettre
2. Ouverture URL + copie données dans presse-papier
3. Confirmation manuelle → mise à jour statut en base

---

## 9. Sécurité — Problèmes et bonnes pratiques

### 9.1 Clés API — Risques critiques

#### ❌ JAMAIS FAIRE

```python
# NE JAMAIS écrire une clé en dur dans le code
CLAUDE_API_KEY = "sk-ant-api03-MaCle..."  # DANGER
```

```bash
# NE JAMAIS committer .env
git add .env  # DANGER — votre clé sera publique sur GitHub
```

#### ✅ TOUJOURS FAIRE

```python
# Charger depuis les variables d'environnement
import os
from dotenv import load_dotenv
load_dotenv()
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
```

#### Que faire si une clé est exposée ?

1. **Révocation immédiate** sur [console.anthropic.com](https://console.anthropic.com) → API Keys → Delete
2. Générer une nouvelle clé
3. Mettre à jour `.env` localement
4. Si sur GitHub : [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning) peut détecter la fuite automatiquement

### 9.2 Mots de passe utilisateur

- Hashés avec **bcrypt** (12 rounds) — irréversible
- Jamais stockés en clair en base ou en mémoire
- Session utilisateur : objet Python en mémoire uniquement (pas de fichier sur disque)

```python
# Implémentation dans auth_service.py
hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
# Vérification
bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
```

### 9.3 Base de données SQLite

- Fichier local `data/sca_data.db` — **jamais committer**
- Ajouté au `.gitignore` automatiquement
- Pas de données personnelles envoyées à l'extérieur, sauf :
  - **Claude API** : reçoit le contenu du profil et la description de l'offre pour le scoring
  - **Adzuna API** : requêtes de recherche uniquement (pas de données personnelles)

### 9.4 Playwright et scraping

- Respectez les CGU des sites scrapés
- Rekrute et Emploi.ma autorisent le scraping non-agressif à usage personnel
- Les sélecteurs CSS sont configurables dans `config.py` si les sites modifient leur structure
- En cas de blocage IP : réduire `SCRAPE_INTERVAL_MINUTES` ou désactiver temporairement la source

### 9.5 Données personnelles (RGPD)

- Toutes les données restent **locales** sur votre machine
- Aucun serveur externe sauf les APIs configurées
- Pour supprimer toutes vos données : effacez `data/sca_data.db`

### 9.6 Recommandations de sécurité supplémentaires

| Mesure | Importance | Comment |
|--------|-----------|---------|
| Mettre à jour les dépendances | Critique | `pip install --upgrade -r requirements.txt` mensuellement |
| Venv isolé | Important | Ne pas installer dans le Python système |
| `.env` en lecture seule | Utile | `chmod 600 .env` (Linux/macOS) |
| Sauvegarder la DB | Important | Copie régulière de `data/sca_data.db` |
| Logs | Utile | Surveiller `logs/sca.log` en cas d'anomalie |

---

## 10. Résolution des problèmes fréquents

### Erreur : `ModuleNotFoundError: No module named 'PyQt6'`

```bash
# S'assurer que le venv est activé
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\Activate.ps1  # Windows

# Réinstaller
pip install PyQt6>=6.6.0
```

### Erreur : `playwright._impl._errors.Error: Executable doesn't exist`

```bash
playwright install chromium
```

### Erreur : `anthropic.AuthenticationError`

- Vérifiez que `CLAUDE_API_KEY` dans `.env` est correcte
- Vérifiez que `.env` est bien à la racine du projet (à côté de `main.py`)
- Testez : `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('CLAUDE_API_KEY', 'VIDE')[:10])"`

### Scraping Rekrute/Emploi.ma retourne 0 offres

Les sélecteurs CSS peuvent avoir changé. Mettez à jour dans `config.py` :

```python
SOURCES = {
    "rekrute": {
        "selectors": {
            "listing": ".nouveau-selecteur",  # Mettre à jour ici
            ...
        }
    }
}
```

### L'application est lente au premier démarrage

Normal — le TF-IDF vectorizer s'initialise et Playwright charge le navigateur. Dès le deuxième lancement, tout est plus rapide.

### Erreur SQLite sur Windows : `database is locked`

```python
# Dans database/db_manager.py, ajouter timeout
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 30})
```

---

## 11. Migration vers la v2 Web

L'architecture est conçue pour une migration web minimale :

```bash
# Seul changement nécessaire : changer DATABASE_URL
DATABASE_URL=postgresql://user:password@localhost:5432/sca_v2
```

- Les **services** (`services/`) fonctionnent tel quel en FastAPI/Django
- Les **modèles** SQLAlchemy sont compatibles PostgreSQL nativement
- Les **migrations** Alembic gèrent le schéma automatiquement
- Seule la couche **UI** doit être réécrite (PyQt6 → React/Vue)

---

## 12. Contribuer

```bash
# Fork + clone
git clone https://github.com/votre-username/sca-desktop.git

# Créer une branche
git checkout -b feature/ma-fonctionnalite

# Linting avant commit
black .
flake8 --max-line-length=120 .

# Tests
pytest tests/ -v

# Pull Request
git push origin feature/ma-fonctionnalite
```

### Standards de code

- **PEP 8** via `black` (ligne max : 120)
- **Aucun import Qt dans `services/`** — règle stricte
- **Docstrings** sur toutes les fonctions publiques
- **Tests unitaires** pour chaque nouveau service

---

## Licence

MIT License — Voir `LICENSE` pour les détails.

---

*SCA Desktop v1.1 — Mars 2026 — Conçu pour automatiser votre recherche de stage avec éthique et efficacité.*
