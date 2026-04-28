# SIEM Manuel M365 - Documentation Utilisateur

**Version**: 1.1.0  
**Date**: 2026-04-11

---

## 1. Introduction

### 1.1 À quoi sert ce SIEM ?

Le SIEM (Security Information and Event Management) Manuel M365 est une solution de sécurité pour Microsoft 365 qui permet de :

- **Collecter** les logs de connexion (SignIns) depuis Microsoft 365
- **Détecter** les utilisateurs non autorisés (hors Truth List)
- **Analyser** les incidents et comportements à risque
- **Gérer** les utilisateurs du portail (admin)
- **Archiver** automatiquement les données anciennes
- **Exporter** des rapports pour la direction

### 1.2 Public cible

- **Administrateurs IT** : Gestion du SIEM, configuration, maintenance
- **Responsable Sécurité** : Surveillance quotidienne, analyse des alertes
- **Direction** : Rapports KPIs, tendances de sécurité

---

## 2. Installation

### 2.0 Git et Sauvegardes (recommandé)

Installer Git :

```powershell
# Windows
winget install --id Git.Git -e
```

```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt update && sudo apt install -y git
```

Initialiser le dépôt dans V2 :

```bash
git init -b main
git add .
git commit -m "chore: initial V2 baseline"
```

Créer un snapshot source manuel :

```bash
python scripts/backup_snapshot.py --keep 14
```

Planifier un backup quotidien sous Windows :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_backup_task.ps1 -DailyAt "20:00" -Keep 14
```

Notes:
- Les snapshots n'incluent pas les DB, backups runtime, `.env` et données sample confidentielles.
- La politique d'exclusion est définie dans `.gitignore` et `scripts/backup_snapshot.py`.

### 2.1 Prérequis

| Logiciel | Version Minimum |
|---------|----------------|
| Python | 3.11+ |
| Windows | 10/11 |
| Linux | Distribution récente |
| macOS | 12+ |

### 2.2 Étapes d'installation

#### Étape 1 : Télécharger le package

```bash
# Cloner ou télécharger le projet
git clone https://github.com/votre-repo/siem-m365.git
cd siem-m365
```

#### Step 2 : Créer l'environnement virtuel

```bash
python -m venv venv
```

#### Step 3 : Activer l'environnement

```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### Step 4 : Installer les dépendances

```bash
cd backend
pip install -r requirements.txt
```

#### Step 5 : Configurer le fichier .env

Copier `.env.example` vers `.env` et configurer :

```env
# Application
APP_NAME=SIEM_M365
APP_ENV=production
DEBUG=False

# Security - CHANGEZ CES CLÉS EN PRODUCTION !
DB_ENCRYPTION_KEY=votre-cle-secrete-32-caracteres
JWT_SECRET_KEY=votre-jwt-secret-32-caracteres
BACKUP_ENCRYPTION_KEY=votre-backup-key-32-car

# Database
DB_PATH=./data/db/siem_hot.db
DB_ARCHIVE_PATH=./data/db/siem_archive.db
DB_CONFIG_PATH=./data/db/siem_config.db

# Backup
BACKUP_PATH=./data/backups
```

#### Step 6 : Initialiser les bases de données

```bash
python ../scripts/init_db.py
```

---

## 3. Activation et Démarrage

### 3.0 CI Multi-OS

Un pipeline GitHub Actions vérifie le projet sur Windows, Linux et macOS :

- Fichier workflow : `.github/workflows/ci-cross-platform.yml`
- Étapes : setup Python 3.12, bootstrap `scripts/start_siem.py --setup-only`, smoke test `scripts/test_all.py`

Pour des environnements avec mot de passe admin personnalisé, vous pouvez fournir :

- `SIEM_TEST_USERNAME`
- `SIEM_TEST_PASSWORD`

### 3.1 Démarrage Automatisé Cross-Platform (recommandé)

Un script de bootstrap Python multi-OS est disponible dans `scripts/start_siem.py`.

Il réalise automatiquement :
- Création du virtualenv `.venv` (si absent)
- Installation des dépendances backend
- Vérification/initialisation des bases SQLite
- Lancement de l'API FastAPI (uvicorn)

Utilisation :

```bash
python scripts/start_siem.py
```

Options utiles :

```bash
# Setup seulement (sans lancer l'API)
python scripts/start_siem.py --setup-only

# Port personnalisé
python scripts/start_siem.py --port 5050

# Eviter un conflit si 5000 est deja occupe
python scripts/start_siem.py --port 5051
```

### 3.2 Démarrage Automatisé Windows (PowerShell)

Un script de bootstrap est disponible pour Windows dans `scripts/start_siem.ps1`.

Il réalise automatiquement :
- Vérification de Python 3.11+
- Création du virtualenv `.venv` (si absent)
- Installation des dépendances backend
- Vérification/initialisation des bases SQLite
- Lancement de l'API FastAPI (uvicorn)

Utilisation :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_siem.ps1
```

Options utiles :

```powershell
# Port personnalisé
powershell -ExecutionPolicy Bypass -File .\scripts\start_siem.ps1 -Port 5050

# Ignorer l'installation automatique de Python si absent
powershell -ExecutionPolicy Bypass -File .\scripts\start_siem.ps1 -SkipPythonInstall
```

### 3.3 Mode Service (background + auto-restart)

Pour un démarrage type production sous Windows (processus en arrière-plan, logs, redémarrage automatique après crash), utiliser :

```powershell
# Démarrer le service local
powershell -ExecutionPolicy Bypass -File .\scripts\start_siem_service.ps1

# Démarrer sur un port personnalisé
powershell -ExecutionPolicy Bypass -File .\scripts\start_siem_service.ps1 -Port 5050

# Arrêter le service
powershell -ExecutionPolicy Bypass -File .\scripts\stop_siem_service.ps1
```

Détails techniques :
- PID du contrôleur : `.runtime/SIEM-M365.pid`
- Flag d'arrêt propre : `.runtime/SIEM-M365.stop`
- Log runtime : `logs/SIEM-M365.log`
- Le script `start_siem_service.ps1` exécute d'abord la phase setup (`start_siem.ps1 -SetupOnly`) puis lance uvicorn dans une boucle de supervision.

### 3.4 Démarrage de l'API

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 5000 --reload
```

L'API est accessible à : `http://127.0.0.1:5000`

### 3.5 Page de connexion

Ouvrir un navigateur : `http://127.0.0.1:5000`

**Identifiants par défaut** :
- Username : `admin`
- Password : `Admin@SIEM2024!`

⚠️ **IMPORTANT** : Changer immediatement le mot de passe admin !

### 3.6 Créer un utilisateur

1. Se connecter en tant qu'admin
2. Aller dans Settings > Users
3. Cliquer sur "Add User"
4. Remplir le formulaire
5. Choisir le rôle (Admin ou Viewer)

### 3.7 Frontend Modulaire V2

Le frontend est maintenant découpé en modules servis par FastAPI :

- `frontend/src/app.js` : contrôleur principal et navigation
- `frontend/src/api.js` : appels API backend
- `frontend/src/views.js` : rendu des vues
- `frontend/src/state.js` : état de session frontend
- `frontend/assets/styles.css` : style global

Fonctionnalités UI V2 déjà migrées :

- Navigation modulaire: Dashboard, Ingestion, SignIns, Risky, Incidents, Audit, SOC, Alertes, Admin
- Pagination: SignIns, Risky, Incidents, Audit, SOC anomalies
- Actions admin: clear-data, activation/desactivation utilisateur, reset password
- Filtres avancés: SignIns, Risky, Incidents, Audit, SOC
- Export SOC: rapport HTML téléchargeable depuis l'interface
- Workflow alertes: approve/reject des nouveaux utilisateurs hors Truth List

Test local des assets :

```bash
python scripts/test_frontend_assets.py
```

---

## 4. Logique Métier

### 4.1 Flux Quotidien

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUX QUOTIDIEN DU SIEM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. EXPORT LOGS M365                                            │
│     └──► Admin exporte SignIn, Risky Users, Incidents          │
│         depuis Microsoft 365 Admin Center                      │
│                                                                 │
│  2. INGESTION                                                     │
│     └──► Upload des fichiers JSON dans le SIEM                  │
│         └──► Déduplication automatique (par event_id)            │
│                                                                 │
│  3. DÉTECTION                                                    │
│     └──► Comparaison avec Truth List                               │
│         └──► Alerte si nouvel utilisateur détecté                  │
│                                                                 │
│  4. ANALYSE                                                      │
│     └──► Dashboard IT : requêtes, filtres                        │
│         └──► Dashboard Direction : KPIs, tendances               │
│                                                                 │
│  5. ARCHIVE                                                      │
│     └──► Auto: HOT (0-90j) → Archive (90-180j)                  │
│         └──► Backup ZIP chiffré après 90j dans Archive          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Détection des Nouveaux Utilisateurs

**Principe** :
1. La **Truth List** contient les utilisateurs autorisés
2. À chaque ingestion de SignIns, le SIEM vérifie si l'utilisateur est dans la Truth List
3. Si **non trouvé** → une **alerte** est générée
4. L'administrateur peut **approuver** (ajouter à la Truth List) ou **rejeter** l'alerte

```
Utilisateur Connecté
        │
        ▼
   Dans Truth List ? ──Non──► ALERTE GENEREE
        │                           │
       Oui                         ▼
        │                    Revue Admin
        ▼                           │
   CONNEXION OK ◄─────────────Approuver/Rejeter
```

### 4.3 Archive Automatique

**CYCLE DE VIE DES DONNÉES** :

| Période | Base | Opérations |
|---------|------|-------------|
| 0-90 jours | HOT | Lecture + Écriture |
| 90-180 jours | ARCHIVE | Lecture seule |
| > 180 jours | BACKUP ZIP | Restaurable si besoin |

**État actuel Phase 2 du backup/restore** :
- Backup manuel déclenchable depuis l'interface Lifecycle ou l'API
- Snapshot cohérent multi-bases : `HOT`, `ARCHIVE`, `CONFIG`
- Archive chiffrée `AES-256-GCM` au format conteneur `.sbk`
- `manifest.json` embarqué dans la charge utile interne
- Intégrité renforcée avec `SHA-256` et `MD5` sur l'archive finale, plus `SHA-256` par fichier interne
- Restore dry-run : déchiffrement, validation du manifest, extraction dans un dossier isolé, sans écrasement de la base active

**Préparation Phase 3 - restauration active contrôlée** :
- Endpoint de restauration active disponible pour `HOT` et `ARCHIVE`
- Confirmation explicite opérateur requise avant activation
- Snapshot de rollback créé avant remplacement des bases runtime
- Endpoint de rollback opérateur disponible pour revenir au snapshot précédent
- La base `CONFIG` reste exclue du restore actif live à ce stade pour éviter d'écraser la base de session courante
- Rotation/rétention automatique active sur archives `.sbk` et snapshots de rollback

**Limites connues à ce stade** :
- Pas encore de job automatique complet HOT -> ARCHIVE -> BACKUP
- Pas encore de restauration active live de la base `CONFIG`
- Rétention pilotée par configuration (`BACKUP_RETENTION_*`, `ROLLBACK_RETENTION_*`) sans planificateur externe dédié

### 4.4 Roles et Permissions

| Rôle | Permissions |
|------|-------------|
| **Admin** | Tout faire : upload, backup, cleanup, users |
| **Viewer** | Lecture seule : query, dashboard, export |

### 4.5 Logique SOC (Security Operations Center)

Le module SOC corrèle automatiquement les données SignIns, Risky Users et Incidents.

Détections implémentées :
- `out-of-list` : connexion depuis un pays hors liste autorisée
- `risk-user` : connexion d'un utilisateur marqué à risque élevé
- `fail-spike` : pic d'échecs d'authentification (10+ en 5 minutes)
- `concurrent-ip` : connexions rapprochées depuis des IP différentes
- `vpn-absent` : connexion hors pays autorisés sans contexte VPN explicite
- `atypical-hours` : connexion réussie en dehors de la plage horaire métier (06:00-22:00)

Pipeline SOC :
1. Sélection d'une période (`today`, `last_7_days`, `last_30_days`, `custom`)
2. Exécution des règles de détection
3. Corrélation temporelle avec incidents proches
4. Déduplication et sauvegarde en `soc_anomalies`
5. Restitution : résumé exécutif, liste paginée, géographie, export HTML

Interface SOC (onglet `SOC Report`) :
- Sélection de période et plage custom
- Bouton `Run Analysis`
- KPIs SOC (anomalies, criticité, taux d'échec, out-of-list)
- Anomalies paginées + filtres (type, sévérité)
- Vue géographique (top pays + pays hors liste)
- Export HTML du rapport SOC

Note d'usage :
- Si les données chargées proviennent d'exports plus anciens, `last_7_days` peut légitimement retourner 0 résultat. Utiliser `last_30_days` ou une plage `custom` alignée sur les dates d'import.

---

## 5. Guide d'Utilisation Quotidienne

### 5.1 Matin - Check Sécurité (5 min)

1. Ouvrir le dashboard : `http://127.0.0.1:5000`
2. Vérifier les **KPIs** (connexions, taux succès, utilisateurs à risque, incidents)
3. Consulter les **tendances** sur les 30 derniers jours
4. Consulter les **alertes** (nouveaux utilisateurs)

### 5.2 Navigation dans l'interface

| Onglet | Description |
|-------|-------------|
| **Dashboard** | KPIs, tendances, export PDF |
| **Ingestion** | Upload des fichiers JSON/CSV (SignIns, Truth List, Risky Users, Incidents, Audit Logs) |
| **SignIns** | Historique des connexions |
| **Risky Users** | Utilisateurs à risque détectés |
| **Incidents** | Incidents de sécurité |
| **Audit Logs** | Journal d'audit M365 avec filtres et pagination |
| **SOC Report** | Analyse SOC, anomalies, géographie, export HTML |
| **Truth List** | Liste des utilisateurs autorisés |
| **Alertes** | Utilisateurs non autorisés détectés |
| **Admin** | Créer/gérer les utilisateurs du portail (admin uniquement) |
| **Profil** | Changer son mot de passe |

### 5.3 Upload des Données

1. Aller dans l'onglet **Ingestion**
2. Sélectionner le bon type d'import : SignIns, Risky Users, Incidents, Truth List ou Audit Logs
3. Cliquer sur "Choisir un fichier" pour sélectionner un JSON ou un CSV selon la source
4. Cliquer sur "Téléverser" pour importer
5. Les données sont dédupliquées automatiquement par event_id/incident_id ou clés métier équivalentes

Conseils pratiques :
- Les exports M365 historiques doivent ensuite etre consultés avec une période cohérente dans l'interface, par exemple `last_30_days` ou `custom`.
- Le répertoire [backend/sample_data/README_SENSITIVE.md](backend/sample_data/README_SENSITIVE.md) documente pourquoi V2 ne distribue pas de jeux de données réels.

### 5.4 Semaine - Analyse (30 min)

1. Générer le rapport HTML :
   - Bouton "Exporter PDF" dans le Dashboard
2. Analyser les **tendances**
3. Exporter les données pour audit :
   - `/api/v1/export/signins/csv`

### 5.5 Gestion des Utilisateurs (Admin)

1. Aller dans l'onglet **Admin**
2. La table affiche tous les utilisateurs créés
3. **Reset PW** : Réinitialiser le mot de passe d'un utilisateur
4. **Activer/Désactiver** : Activer ou désactiver un compte

### 5.6 Mensuel - Maintenance

1. Vérifier les backups : `/api/v1/lifecycle/backups`
2. Vérifier l'intégrité d'un backup : `/api/v1/lifecycle/backup/{backup_id}/verify`
3. Tester un restore isolé : `/api/v1/lifecycle/backup/{backup_id}/restore`
4. Si nécessaire, lancer une restauration active contrôlée : `/api/v1/lifecycle/backup/{backup_id}/restore/activate`
5. En cas de problème post-restore, déclencher le rollback opérateur : `/api/v1/lifecycle/rollback/{rollback_id}`
6. Mettre à jour la Truth List

---

## 6. Endpoints API Importants

### 6.1 Authentification

| Endpoint | Méthode | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | Connexion |
| `/api/v1/auth/logout` | POST | Déconnexion |
| `/api/v1/auth/me` | GET | Info utilisateur |
| `/api/v1/auth/register` | POST | Créer utilisateur (admin) |
| `/api/v1/auth/change-password` | POST | Changer son mot de passe |
| `/api/v1/auth/users` | GET | Liste utilisateurs (admin) |
| `/api/v1/auth/reset-password` | POST | Reset mot de passe user (admin) |
| `/api/v1/auth/toggle-user` | POST | Activer/désactiver user (admin) |

### 6.2 Ingestion

| Endpoint | Méthode | Description |
|----------|--------|-------------|
| `/api/v1/ingest/upload/signins` | POST | Upload SignIns |
| `/api/v1/ingest/upload/risky-users` | POST | Upload Risky Users |
| `/api/v1/ingest/upload/incidents` | POST | Upload Incidents |
| `/api/v1/ingest/upload/audit-logs` | POST | Upload Audit Logs |
| `/api/v1/ingest/upload/truth-list` | POST | Upload Truth List |

### 6.3 Requêtes

| Endpoint | Méthode | Description |
|----------|--------|-------------|
| `/api/v1/query/signins` | GET | Rechercher SignIns |
| `/api/v1/query/risky-users` | GET | Rechercher Risky Users |
| `/api/v1/query/incidents` | GET | Rechercher Incidents |
| `/api/v1/query/audit-logs` | GET | Rechercher Audit Logs M365 |
| `/api/v1/query/truth-list` | GET | Rechercher Truth List |
| `/api/v1/dashboard/kpis` | GET | KPIs dashboard |
| `/api/v1/dashboard/trends` | GET | Tendances |
| `/api/v1/dashboard/kpi-drilldown` | GET | Détail d'un KPI (table filtrée) |

### 6.4 Alertes

| Endpoint | Méthode | Description |
|----------|--------|-------------|
| `/api/v1/alerts/unknown-users` | GET | Utilisateurs non autorisés |

### 6.5 Export

| Endpoint | Méthode | Description |
|----------|--------|-------------|
| `/api/v1/export/signins/csv` | GET | Export SignIns CSV |
| `/api/v1/export/risky-users/csv` | GET | Export Risky Users CSV |
| `/api/v1/export/incidents/csv` | GET | Export Incidents CSV |
| `/api/v1/export/pdf` | GET | Rapport HTML |
| `/api/v1/dashboard/director-pdf` | GET | Rapport Direction |

### 6.6 Lifecycle

| Endpoint | Méthode | Description |
|----------|--------|-------------|
| `/api/v1/lifecycle/status` | GET | Statut archive |
| `/api/v1/lifecycle/backup/create` | POST | Créer un backup cohérent multi-bases chiffré AES-256-GCM |
| `/api/v1/lifecycle/backups` | GET | Liste backups |
| `/api/v1/lifecycle/logs` | GET | Historique des opérations backup/restore |
| `/api/v1/lifecycle/backup/{backup_id}/contents` | GET | Inspecter le contenu du ZIP et son manifest |
| `/api/v1/lifecycle/backup/{backup_id}/verify` | POST | Vérifier les checksums MD5/SHA-256 et le manifest |
| `/api/v1/lifecycle/backup/{backup_id}/restore` | POST | Restore dry-run dans un dossier isolé |
| `/api/v1/lifecycle/backup/{backup_id}/restore/activate` | POST | Restore actif contrôlé de HOT et ARCHIVE |
| `/api/v1/lifecycle/rollback/{rollback_id}` | POST | Rollback opérateur vers le snapshot pré-restore |
| `/api/v1/lifecycle/retention/run` | POST | Exécuter manuellement la rotation/rétention |
| `/api/v1/lifecycle/import` | POST | Importer un fichier .sbk existant dans une nouvelle instance |

### 6.6.1 Contenu d'un backup chiffré

Chaque archive chiffrée `.sbk` encapsule une archive interne contenant :

- `hot.db`
- `archive.db`
- `config.db`
- `manifest.json`

Le `manifest.json` embarque :

- l'identifiant du backup
- la version de format
- le périmètre du backup
- les checksums SHA-256 des fichiers internes
- les compteurs de données sauvegardées

### 6.6.2 Smoke test de validation backup/restore

Le projet contient un smoke test bout-en-bout :

```bash
python scripts/test_backup_restore_flow.py
```

Le test exécute :

- login admin
- création d'un backup chiffré
- inspection du backup
- vérification d'intégrité
- restore dry-run
- restore actif contrôlé
- rollback opérateur

### 6.6.3 Import d'un backup existant (déploiement nouveau serveur)

**Scénario** : Vous avez un backup `.sbk` d'une ancienne instance et vous voulez le restaurer dans une nouvelle instance vierge.

**Procédure** :

1. **Déployer une nouvelle instance** avec une base de données vierge
2. **Accéder à l'interface** : `http://127.0.0.1:5000`
3. **Se connecter** en tant qu'admin
4. **Aller à l'onglet Lifecycle**
5. **Dans la section "Import Backup"** :
   - Cliquer sur "Sélectionner un fichier"
   - Choisir le fichier `.sbk`
   - Cliquer sur "Importer"
6. **Attendre le chargement** (indiqué par "Chargement en cours...")
7. **Vérifier l'import** : Le backup apparaît dans la liste avec le statut `imported`
8. **Les données sont maintenant disponibles** :
   - Tables HOT, ARCHIVE, CONFIG peuplées depuis le backup
   - Retention automatique activée selon les politiques configurées
   - Tous les backups disponibles pour inspection/restore

**Via API** (curl) :

```bash
curl -X POST http://127.0.0.1:5000/api/v1/lifecycle/import \
  -H "Authorization: Bearer <your_token>" \
  -F "file=@/path/to/backup_20260411_143000.sbk"
```

**Réponse succès** :

```json
{
  "status": "success",
  "backup_id": "backup_20260411_143000",
  "records": 45230,
  "size_bytes": 3500000,
  "manifest_id": 42,
  "encryption_method": "AES-256-GCM",
  "message": "Backup backup_20260411_143000 importé avec succès (45230 enregistrements)"
}
```

**Notes** :

- L'endpoint valide le format `.sbk`, décrypte le fichier et vérifie son intégrité
- Si l'ID du backup existe déjà, l'import est rejeté (évite les doublons)
- Le fichier importé est stocké dans `data/backups/archives/`
- Une entrée `ArchiveManifest` est créée en base pour enregistrer le backup
- Un log `IMPORT_BACKUP` est ajouté à l'historique des opérations

### 6.7 SOC

| Endpoint | Méthode | Description |
|----------|--------|-------------|
| `/api/v1/soc/analyze` | POST | Exécuter l'analyse SOC sur la période |
| `/api/v1/soc/summary` | GET | Récupérer le résumé exécutif SOC |
| `/api/v1/soc/anomalies` | GET | Lister les anomalies SOC (pagination + filtres) |
| `/api/v1/soc/users/{user_principal}` | GET | Profil de risque SOC d'un utilisateur |
| `/api/v1/soc/export/html` | POST | Exporter le rapport SOC en HTML |

### 6.8 KPIs Dashboard - Détails disponibles

Les cartes KPI ci-dessous supportent `Voir details` et affichent une table filtrée :

- `external_suspicious_ips`
- `blocked_attempts`
- `out_of_country_rate`
- `risky_users`
- `atypical_hours` (uniquement les anomalies SOC de type `atypical-hours`)

---

## 7. Dépannage

### 7.1 Login échoue

1. Vérifier le username/password
2. Vérifier que l'utilisateur n'est pas verrouillé (5 échecs)
3. Contacter un admin pour unlock

### 7.2 Upload échoue

1. Vérifier le format JSON (valide)
2. Vérifier la taille (< 50MB)
3. Vérifier les champs requis
4. Vérifier que le type d'import choisi correspond bien au fichier envoyé

### 7.3 Le serveur ne démarre pas sur le port 5000

1. Vérifier si une autre instance tourne déjà sur `http://127.0.0.1:5000`
2. Relancer avec un autre port, par exemple `python scripts/start_siem.py --port 5051`
3. Mettre à jour l'URL d'accès dans le navigateur en conséquence

### 7.4 Performance lente

- Réduire la période de dates dans les filtres
- Utiliser la pagination
- Limiter les exports à 10k records

---

## 8. Contacts et Support

- **Email support** : support@entreprise.com
- **Documentation** : `/docs`
- **Admin IT** : Voir Settings > Users

---

## 9. Fonctionnalités v1.1.0

### Nouvelles fonctionnalités ajoutées depuis v1.0.0

- **Dashboard étendu** : Boutons Export PDF et Rafraîchir, section Tendances
- **Onglets新增** : Risky Users, Incidents visibles dans le menu
- **Gestion utilisateurs** : Table avec Reset Password et Toggle Actif/Inactif
- **API admin** : CRUD complet sur les utilisateurs
- **Truth List endpoint** : `/query/truth-list` pour afficher les utilisateurs autorisés
- **Export HTML** : Génération de rapport via `/export/pdf`

### Fichiers de données sample

V2 ne fournit pas de jeux de données réels dans le dépôt.

- Le répertoire [backend/sample_data/README_SENSITIVE.md](backend/sample_data/README_SENSITIVE.md) explique cette contrainte.
- N'ajouter ici que des fichiers synthétiques ou anonymisés.
- Pour des validations fonctionnelles, charger vos propres exports M365 ou des jeux de test assainis.

---

*Document généré le 2026-04-11*  
*SIEM Manuel M365 v1.1.0*
