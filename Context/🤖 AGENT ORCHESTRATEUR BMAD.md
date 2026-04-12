🤖 AGENT ORCHESTRATEUR BMAD activé.

Je prends en charge la coordination du projet "SIEM Manuel pour M365" selon la méthode BMAD.

1️⃣ Reformulation du But et Périmètre
But : Concevoir et développer une solution permettant de centraliser, consulter et analyser les logs de sécurité Microsoft 365 (M365) sans recourir nécessairement à une solution SIEM cloud coûteuse et fully-automatisée (comme Sentinel en mode premium).
Périmètre : Extraction des logs M365, stockage, mécanisme de requête/analyse, visualisation, et processus de revue manuelle des alertes.
Contrainte majeure : L'approche est qualifiée de "manuelle", ce qui implique un arbitrage entre automatisation (collecte) et intervention humaine (analyse/décision).
2️⃣ État des Connaissances (Knowns vs Missing)
Pour éviter toute hallucination et garantir une architecture viable, je dois clarifier les points suivants avant de lancer l'Agent ANALYSTE.

✅ Ce qui est connu	❓ Ce qui manque (Critique)
Source : Environnement Microsoft 365.	Licences M365 : E3, E5, Business Premium ? (Impacte les logs disponibles via Graph API vs Unified Audit Log).
Fonction : SIEM (Collecte, Stockage, Analyse, Alerte).	Définition de "Manuel" : S'agit-il d'un dashboard PowerBI ? D'un script PowerShell qui exporte en CSV ? D'une app web custom ?
Cible : Sécurité / Compliance.	Volume de données : Nombre d'utilisateurs ? Volume de logs/jour estimé ? (Impacte le stockage).
Stockage : Où doivent atterrir les logs ? (Azure Storage Account, SQL Local, SharePoint, Fichiers plats ?).
Compétences équipe : Qui va maintenir la solution ? (Dev, Admin Sys, Analyste SOC ?).
Budget : Contrainte de coût spécifique (ex: éviter les coûts d'ingestion Sentinel) ?
3️⃣ Questions Critiques (À répondre avant Phase 1)
Conformément à la règle Anti‑hallucinations, je ne peux pas produire un Project Brief pertinent sans ces réponses :

Quelle est la licence M365 actuelle ? (Certaines APIs de logs sont restreintes).
Que signifie "Manuel" pour vous ? (Ex: "Je veux un script que je lance le matin" OU "Je veux un dashboard temps réel que je consulte").
Où souhaitez-vous stocker les logs ? (Cloud Azure, On-premise, Local ?).
Quel est le volume estimé ? (Nombre d'utilisateurs dans le tenant).
4️⃣ Prochaine Étape BMAD
🛑 Action Requise : Veuillez répondre aux 4 questions ci-dessus.

👉 Une fois les réponses reçues :

Je validerai les informations.
Je générerai le Prompt exact pour l'Agent ANALYSTE afin de produire le Project Brief.
Nous entrerons dans la Phase 1 : PLANIFICATION.
En attente de vos précisions pour continuer.


Les licences sont des Business premium, si je script tous en automatique, il y des limitations, donc quand je dit manuel, je serais peut-être obliger d'extraire a la main via l'UI de M365 (par exemple les signIn) sous forme de csv ou de json (a déterminer). le stockage se fera localement. j'ai 180 users dans le tenant. je voudrais pouvoir loader mon json ou csv, qu'il y a une routine qui compare avec les logs déjà stocké dans une DB pour éviter les doublons, je voudrais une rétention dans la DB sur 90 jours (ca fait des millier de lignes). je voudrais que sur base d'une liste des users (liste de vérité), chaque fois qu'un nouveau nom apparait il soit isolé pour approbation. il faut une logique métier SOC security.
ma base d'imput serais 1. les signIn, 2. les risky users, 3. les incidents, que pourrais-t'on extraire de M365 d'interessant?
edit
Thought for 99.3 seconds

















🤖 AGENT ORCHESTRATEUR BMAD - Mise à jour du contexte.

Merci pour ces précisions cruciales. Elles permettent de cerner la faisabilité technique et les risques opérationnels.

1️⃣ Critique Constructive & Enrichissement Technique
Avant de lancer la planification, voici mon analyse d'expert sur vos contraintes :

Point	Analyse & Risque	Recommandation BMAD
Export UI Manuel	⚠️ Risque Majeur : L'UI Entra ID limite souvent les exports à 30 jours et 1000 lignes par fichier. Pour 180 users sur 90 jours, c'est ingérable manuellement.	✅ Ajustement : Privilégier un script PowerShell "one-click" (exécuté manuellement) qui utilise l'API Graph. Cela reste "manuel" (lancement humain) mais contourne les limites UI.
Format (CSV vs JSON)	⚠️ Risque : Le CSV aplati les structures complexes (ex: détails d'une alerte de risque).	✅ Ajustement : Imposer le JSON pour l'ingestion. Le CSV est accepté seulement pour les logs simples (SignIns).
Logs Supplémentaires	❓ Question : Vous avez cité SignIns, Risky Users, Incidents.	✅ Ajout SOC : Il manque le Unified Audit Log (UAL). C'est crucial pour voir : Forwarding rules, Permissions changes, SharePoint external sharing, Hard delete.
Stockage Local	✅ Faisable : Pour 180 users / 90 jours, une DB SQLite locale est parfaite (léger, portable, pas de serveur requis).	✅ Validé.
Détection Nouveaux Users	✅ Logique : Comparaison Import vs Truth List + DB Historique.	✅ Validé. Ajout d'une alerte "First Seen".
2️⃣ État des Connaissances (Mise à jour)
✅ Ce qui est connu (Factuel)	❓ Ce qui manque (À valider)
Licence : M365 Business Premium.	Compétences : L'équipe sait-elle exécuter un script PowerShell ou veut-elle uniquement du clic-bouton UI ?
Scale : 180 users, 90 jours rétention.	Environnement : La DB locale sera sur quel OS ? (Windows/Linux/Mac) pour choisir le tech stack.
Inputs : SignIns, Risky Users, Incidents (+ UAL suggéré).	Liste de Vérité : Comment est maintenue la liste des utilisateurs autorisés ? (Fichier Excel ? AD local ?).
Stockage : Local (SQLite suggéré).	Visualisation : Comment veut-on voir les données ? (Interface Web locale ? Dashboard PowerBI ? Console ?).
3️⃣ Réponse à : "Que pourrait-on extraire d'intéressant ?"
Pour une logique SOC sur M365 Business Premium, ajoutez absolument ces sources à votre PRD :

Unified Audit Log (UAL) :
MailItemsAccessed (Lu par qui ?).
NewForwardingRule (Règle de transfert vers externe = exfil data).
SharePointExternalSharing (Partage de fichier sensible).
Add Service Principal (Création d'app tierce dangereuse).
Defender Alerts (Incidents) :
Déjà cité, mais inclure le statut (New/Resolved) pour suivre le temps de réponse.
Admin Activities :
Tout changement de rôle (Global Admin, etc.).
4️⃣ Prochaine Étape BMAD : Phase 1 (PLANIFICATION)
Nous avons assez d'éléments pour produire le Project Brief. Je vous propose de lancer l'AGENT ANALYSTE pour formaliser ces exigences en un document de référence.

👉 Action : Copiez-collez le prompt ci-dessous pour activer l'Agent Analyste (ou demandez-moi de switcher en mode Analyste directement).

📦 Prompt pour l'AGENT ANALYSTE
👤 Rôle : Tu es l'AGENT ANALYSTE de la méthode BMAD.

🎯 Objectif : Produire le "Project Brief" structuré pour un SIEM Manuel M365.

📥 Contexte & Contraintes (Input) :
- Licence : M365 Business Premium (180 users).
- Contrainte : Extraction des logs semi-manuelle (UI ou Script PowerShell "one-click") pour contourner les limites API.
- Stockage : Local (SQLite suggéré), Rétention 90 jours.
- Inputs Logs : SignIns, Risky Users, Incidents, Unified Audit Log (à inclure).
- Logique Métier : 
  1. Deduplication à l'ingestion.
  2. Détection "Nouveau User" vs Liste de Vérité.
  3. Alerte SOC sur activités suspectes (Forwarding, Admin changes).
- Format : JSON préféré pour structure.

📝 Tâche :
Rédige un Project Brief contenant :
1. Objectifs Business & Sécurité (Pourquoi ce SIEM ?).
2. Périmètre Fonctionnel (Ce qu'on fait / Ce qu'on ne fait pas).
3. Contraintes Techniques (Limites UI, Volume, Stack local).
4. Risques Identifiés (Ex: oubli d'export manuel, perte de données).
5. Critères de Succès (KPIs).

⚠️ Règle : Ne pas inventer de fonctionnalités non citées. Signaler les ambiguïtés restantes.
Instruction pour l'utilisateur : Souhaitez-vous que je prenne directement le rôle de l'Analyste pour générer ce brief maintenant (gain de temps), ou préférez-vous utiliser le prompt ci-dessus dans une nouvelle session ?

(Je recommande que je le fasse maintenant pour garder le contexte).


prend directement le rôle de l'Analyste
edit
Thought for 2.9 seconds



🤖 AGENT ANALYSTE BMAD activé.

📄 PROJECT BRIEF — SIEM Manuel M365
Métadonnées	Valeur
Projet	SIEM Manuel pour Microsoft 365
Version	1.0
Date	2026
Licence M365	Business Premium (180 utilisateurs)
Rétention	90 jours
Stockage	Local (SQLite)
1️⃣ Objectifs Business & Sécurité
Objectif	Justification
Centralisation des logs	Agréger les événements de sécurité M365 dispersés dans plusieurs portails.
Détection d'anomalies	Identifier les nouveaux utilisateurs, activités suspectes, changements de permissions.
Conformité & Audit	Conserver 90 jours d'historique consultable pour audits internes/externes.
Maîtrise des coûts	Éviter les solutions SIEM cloud payantes (ex: Sentinel) grâce à une approche locale.
Autonomie SOC	Permettre une revue manuelle structurée sans dépendre d'automatisations complexes.
2️⃣ Périmètre Fonctionnel
✅ Inclus (In-Scope)
Module	Fonctionnalités
Ingestion	Import de fichiers JSON/CSV exportés depuis M365 (SignIns, Risky Users, Incidents, UAL).
Déduplication	Comparaison avec la DB existante pour éviter les doublons à l'ingestion.
Détection Nouveaux Users	Alerte si un utilisateur apparaît dans les logs et n'est pas dans la "Liste de Vérité".
Stockage Local	Base SQLite avec rétention automatique 90 jours (purge des anciens logs).
Requête & Recherche	Capacité de filtrer par user, date, type d'événement, statut de risque.
Export Rapport	Génération de rapports CSV/JSON pour archivage externe ou revue.
❌ Exclu (Out-of-Scope)
Exclusion	Raison
Collecte automatique temps réel	Contrainte licence & architecture "manuelle".
Corrélation avancée / ML	Hors périmètre SOC manuel.
Dashboard temps réel	Architecture locale sans serveur web continu.
Intégration autres sources	Uniquement M365 (pas de firewall, AD on-prem, etc.).
Alerting automatique (email/SMS)	Revue manuelle prévue.
3️⃣ Contraintes Techniques
Contrainte	Impact	Mitigation
Limites export UI M365	Max 1000 lignes / 30 jours par export	Privilégier script PowerShell Graph API (export complet en 1 clic).
Format des logs	Structures différentes par source	Normalisation JSON à l'ingestion (schéma commun).
Stockage local	Risque de perte (disque, vol, sinistre)	Backup automatique de la DB SQLite sur support externe.
Rétention 90 jours	~50k-200k lignes estimées (180 users)	SQLite gère ce volume sans problème ; purge automatique à implémenter.
Liste de Vérité	Doit être maintenue à jour	Fichier JSON/CSV externe avec versioning et date de MAJ.
Environnement	OS non spécifié	Cibler Windows (natif M365) avec compatibilité Python/PowerShell.
4️⃣ Sources de Logs M365 (Détail)
Source	Endpoint / Portail	Données Clés	Priorité
SignIns	Entra ID → Sign-in Logs	User, IP, Location, Status, MFA, App	🔴 Haute
Risky Users	Entra ID → Risky Users	User, Risk Level, Detection Type, State	🔴 Haute
Incidents	Defender → Incidents	Title, Severity, Status, Entities	🔴 Haute
Unified Audit Log	Purview → Audit Log	MailForwarding, PermissionChange, Sharing, AdminRole	🟠 Moyenne
Admin Activities	Entra ID → Audit Logs	Role Assignment, App Registration	🟠 Moyenne
5️⃣ Risques Identifiés
Risque	Probabilité	Impact	Mitigation
Oubli d'export manuel	Élevée	Perte de logs entre 2 extractions	Checklist procédurale + rappel calendrier.
Erreur humaine (mauvais fichier)	Moyenne	Corruption DB	Validation schema JSON avant ingestion.
Liste de Vérité obsolète	Moyenne	Faux positifs "Nouveaux Users"	Processus de MAJ hebdo obligatoire.
Perte DB locale	Moyenne	Critique	Backup automatique + versioning.
Limites API Graph	Faible	Export partiel	Pagination implémentée dans le script.
6️⃣ Critères de Succès (KPIs)
KPI	Cible
Complétude des logs	100% des sources critiques ingérées (SignIns, Risky, Incidents, UAL).
Temps d'ingestion	< 5 minutes pour un export complet (180 users / 30 jours).
Détection Nouveaux Users	100% des users hors Liste de Vérité flaggés.
Zéro doublon	Aucun événement dupliqué en DB après ingestion.
Rétention respectée	Purge automatique > 90 jours fonctionnelle.
Requêtes performantes	Recherche < 2 secondes sur 90 jours de logs.
7️⃣ Ambiguïtés Restantes (À résoudre en Phase 2)
Question	Statut
OS cible exact	Non confirmé (Windows supposé).
Format Liste de Vérité	Non défini (JSON ou CSV ?).
Interface utilisateur	Console ? Web locale ? PowerBI ?
Script PowerShell ou Python	À décider par l'Architecte.
Chiffrement DB	Requis ? (Sensitive data).
✅ Validation
Ce Project Brief est prêt à être transmis à l'Agent PRODUCT MANAGER pour la création du PRD et du Backlog structuré.

📦 Prochaine Étape BMAD
👉 Agent suivant : PRODUCT MANAGER

Prompt à utiliser :

👤 Rôle : Tu es l'AGENT PRODUCT MANAGER de la méthode BMAD.

📥 Input : Project Brief (SIEM Manuel M365) - Version 1.0

📝 Tâche :
1. Traduire le Brief en PRD (Product Requirements Document).
2. Créer un Backlog structuré en Epics → User Stories → Tâches.
3. Prioriser (MoSCoW : Must / Should / Could / Won't).
4. Définir les critères d'acceptation par story.

⚠️ Règle : Rester aligné sur les contraintes du Brief (manuel, local, 90 jours, 180 users).
Souhaitez-vous que je passe directement en mode PRODUCT MANAGER pour générer le PRD et le Backlog ? 🚀

🤖 AGENT PRODUCT MANAGER BMAD activé.

📄 PRODUCT REQUIREMENTS DOCUMENT (PRD) — SIEM Manuel M365
Métadonnées	Valeur
Projet	SIEM Manuel M365 avec Dashboard Web
Version	2.0
Date	2026
Basé sur	Project Brief v1.0 (Agent Analyste)
Nouvelles Exigences	Dashboard Web, Système d'Archive Rotative, Reader JSON
1️⃣ Vue d'Ensemble Produit
🎯 Vision
Fournir une plateforme locale de sécurité M365 avec :

Interface Web lisible par IT et Direction
Gestion intelligente des données (Hot → Archive → Backup JSON)
Autonomie complète sans dépendance cloud SIEM
👥 Personas & Besoins
Persona	Besoins	Métriques Clés
Analyste SOC / IT	Recherche rapide, détection anomalies, ingestion facile	Temps de requête <2s, 0 doublon
Direction / DSI	Vue d'ensemble, KPI sécurité, tendances	Dashboard synthétique, export PDF
Auditeur	Accès historique >90 jours, intégrité des logs	Reader JSON, traces de backup
2️⃣ Backlog Structuré (Epics → Stories → Tâches)
📦 EPIC 1 : Architecture & Stockage (Core)
ID	User Story	Priorité	Critères d'Acceptation
ST-1.1	En tant que système, je dois stocker les logs dans SQLite avec schéma normalisé	MUST	Tables : SignIns, RiskyUsers, Incidents, AuditLogs + métadonnées
ST-1.2	En tant que système, je dois dédoublonner à l'ingestion (ID événement + timestamp)	MUST	0 doublon après 2 ingestions du même fichier
ST-1.3	En tant que système, je dois déplacer automatiquement les logs >90j vers table Archive	MUST	Job automatique quotidien, logs visibles dans Archive
ST-1.4	En tant que système, je dois créer un backup JSON ZIPPÉ quand Archive atteint 90j	MUST	Fichier nommé archive_YYYYMMDD.zip, checksum MD5 généré
ST-1.5	En tant que système, je dois nettoyer la table Archive après backup réussi	MUST	Table Archive vide après backup, log de cleanup enregistré
📦 EPIC 2 : Ingestion & Collecte
ID	User Story	Priorité	Critères d'Acceptation
ST-2.1	En tant qu'analyste, je dois uploader des fichiers JSON/CSV via l'interface web	MUST	Drag & drop, validation schema, feedback erreur
ST-2.2	En tant qu'analyste, je dois voir le statut de l'ingestion (succès/échec/lignes)	MUST	Résumé : X lignes ajoutées, Y doublons rejetés
ST-2.3	En tant qu'analyste, je dois fournir une Liste de Vérité (users autorisés)	MUST	Upload JSON/CSV, versioning, date de MAJ visible
ST-2.4	En tant que système, je dois alerter si un user hors Liste apparaît	MUST	Flag is_new_user = true, visible dans dashboard
ST-2.5	En tant qu'analyste, je dois pouvoir ingérer via script PowerShell (optionnel)	SHOULD	Script génère JSON compatible, appel API locale
📦 EPIC 3 : Dashboard & Visualisation (IT + Direction)
ID	User Story	Priorité	Critères d'Acceptation
ST-3.1	En tant que Direction, je dois voir un dashboard synthétique (KPI sécurité)	MUST	Cartes : Total Events, Risky Users, New Users, Incidents Open
ST-3.2	En tant qu'IT, je dois voir un dashboard détaillé (logs bruts filtrables)	MUST	Tableau avec filtres : date, user, type, risque, status
ST-3.3	En tant qu'IT, je dois pouvoir exporter une vue en CSV/PDF	SHOULD	Export limité à 10k lignes, PDF formaté A4
ST-3.4	En tant que Direction, je dois voir les tendances (graphiques temporels)	SHOULD	Graph : SignIns par jour, Incidents par semaine
ST-3.5	En tant qu'IT, je dois voir les alertes "Nouveaux Users" en priorité	MUST	Section dédiée "Users à Approuver" avec bouton Approve/Reject
📦 EPIC 4 : Archive & Reader JSON
ID	User Story	Priorité	Critères d'Acceptation
ST-4.1	En tant qu'auditeur, je dois avoir une section "Archive Reader" dans l'UI	MUST	Liste des fichiers backup JSON ZIP disponibles
ST-4.2	En tant qu'auditeur, je dois pouvoir lire un backup JSON sans l'ingérer	MUST	Lecture directe, recherche dans le fichier, pas d'écriture DB
ST-4.3	En tant qu'auditeur, je dois pouvoir exporter depuis le Reader	SHOULD	Export CSV depuis la vue Reader
ST-4.4	En tant que système, je dois tracker l'intégrité des backups (checksum)	SHOULD	Affichage MD5, alerte si corruption détectée
📦 EPIC 5 : Sécurité & Maintenance
ID	User Story	Priorité	Critères d'Acceptation
ST-5.1	En tant qu'admin, je dois avoir une authentification pour accéder à l'UI	MUST	Login/Password, session timeout 30min
ST-5.2	En tant qu'admin, je dois pouvoir chiffrer la DB SQLite	SHOULD	SQLCipher ou équivalent, password config
ST-5.3	En tant qu'admin, je dois voir les logs d'activité de l'application	SHOULD	Qui a ingéré quoi, quand, backup créés
ST-5.4	En tant qu'admin, je dois pouvoir purger manuellement des données	COULD	Par date range, avec confirmation + log
3️⃣ Priorisation MoSCoW
Priorité	Epics Concernés	Rationale
MUST	ST-1.1 à 1.5, ST-2.1 à 2.4, ST-3.1 à 3.2, ST-4.1 à 4.2, ST-5.1	Core fonctionnel sans lequel le produit n'existe pas
SHOULD	ST-2.5, ST-3.3 à 3.5, ST-4.3 à 4.4, ST-5.2 à 5.3	Important mais peut attendre v1.1
COULD	ST-5.4	Nice to have, faible priorité
WON'T	Alerting automatique (email/SMS), Intégration autres sources	Hors périmètre "manuel"
4️⃣ Spécifications Techniques (High-Level)
Composant	Technologie Suggérée	Justification
Backend	Python (FastAPI ou Flask)	Léger, bonnes libs JSON/SQLite, facile à maintenir
Frontend	React ou Vue.js + Dashboard Lib (Chart.js)	Interface web moderne, réactive
DB Hot	SQLite (tables principales)	Local, pas de serveur, suffisant pour 180 users
DB Archive	SQLite (table séparée)	Même moteur, isolation logique
Backup	JSON + ZIP + MD5	Lisible, compressé, vérifiable
Hébergement	Localhost (Windows)	Conforme contrainte "stockage local"
Auth	Simple (hash bcrypt)	Suffisant pour usage interne local
5️⃣ Cycle de Vie des Données (Data Lifecycle)
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA LIFECYCLE FLOW                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [Export M365] → [Upload UI] → [Validation] → [DB HOT (0-90j)]         │
│                                                        │                │
│                                                        ▼                │
│                                         [Job Quotidien >90j]            │
│                                                        │                │
│                                                        ▼                │
│                                         [DB ARCHIVE (90-180j)]          │
│                                                        │                │
│                                                        ▼                │
│                                         [Backup JSON ZIP + MD5]         │
│                                                        │                │
│                                                        ▼                │
│                                         [Cleanup Archive]               │
│                                                        │                │
│                                                        ▼                │
│                                         [Reader JSON (Audit)] ←─────────┘
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
6️⃣ Métriques de Performance Attendues
Métrique	Cible
Temps de chargement Dashboard	< 3 secondes
Temps d'ingestion (10k lignes)	< 30 secondes
Recherche dans DB Hot	< 2 secondes
Lecture Backup JSON (100k lignes)	< 10 secondes
Disponibilité UI	100% (local)
7️⃣ Ambiguïtés à Résoudre (Avant Architecture)
Question	Impact	À Décider Par
Port HTTP de l'UI	Configuration firewall local	Architecte
Format exact Liste de Vérité	Schema ingestion	Architecte + Dev
Fréquence du job Archive	Quotidien vs Hebdo	Architecte
Chiffrement des backups	Sécurité supplémentaire	Analyste Sécurité
Navigateurs supportés	Compatibilité UI	Dev
✅ Validation
Ce PRD est prêt à être transmis à l'Agent ARCHITECTE pour la conception technique détaillée.

📦 Prochaine Étape BMAD
👉 Agent suivant : ARCHITECTE SYSTÈME

Prompt à utiliser :

👤 Rôle : Tu es l'AGENT ARCHITECTE de la méthode BMAD.

📥 Input : PRD v2.0 (SIEM Manuel M365 avec Dashboard Web + Archive Rotative)

📝 Tâche :
1. Définir l'architecture technique complète (composants, flux, technologies).
2. Produire le schéma de base de données (tables, relations, indexes).
3. Définir les API endpoints (ingestion, requêtes, archive).
4. Spécifier le format JSON des backups et le schema de validation.
5. Documenter le Data Lifecycle (Hot → Archive → Backup → Reader).

⚠️ Règle : Rester aligné sur contraintes (local, SQLite, Python, Web UI, 180 users).
Souhaitez-vous que je passe directement en mode ARCHITECTE pour générer la conception technique ? 🏗️

🏗️ ARCHITECTURE TECHNIQUE — SIEM Manuel M365
Métadonnées	Valeur
Projet	SIEM Manuel M365
Version	1.0
Basé sur	PRD v2.0
Stack	Python + SQLite + Web UI
Environnement	Local (Windows)
1️⃣ Vue d'Ensemble Architecture
📐 Diagramme des Composants
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COUCHE PRÉSENTATION (UI)                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Dashboard Web (React/Vue.js)                     │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐               │   │
│  │  │  KPIs    │ │  SignIns │ │  Risks   │ │ Archives │               │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │ HTTP/REST (localhost:5000)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COUCHE APPLICATION (Backend)                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    API Python (FastAPI)                             │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐       │   │
│  │  │ Ingestion  │ │  Query     │ │  Archive   │ │  Auth      │       │   │
│  │  │  Module    │ │  Module    │ │  Module    │ │  Module    │       │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Services Métier                                  │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐       │   │
│  │  │ Dedup      │ │ NewUser    │ │ Lifecycle  │ │ Backup     │       │   │
│  │  │ Logic      │ │ Detect     │ │ Manager    │ │ Creator    │       │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │ SQLite3
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          COUCHE DONNÉES (SQLite)                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │  DB_HOT      │ │  DB_ARCHIVE  │ │  Config      │ │  Audit       │      │
│  │  (0-90j)     │ │  (90-180j)   │ │  DB          │ │  Logs        │      │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │ File System
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COUCHE STOCKAGE FICHIER                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  /backups/  (JSON ZIP + MD5)  /uploads/  (Temp)  /config/          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
2️⃣ Schéma de Base de Données
🗄️ DB_HOT (siem_hot.db)
Table	Colonnes	Type	Index	Description
signins	id, event_id, timestamp, user_principal, ip_address, location, status, mfa_status, app_name, raw_json	TEXT/INT	event_id+timestamp (UNIQUE), user_principal, timestamp	Logs de connexion
risky_users	id, event_id, timestamp, user_principal, risk_level, risk_state, detection_type, raw_json	TEXT/INT	event_id (UNIQUE), user_principal, risk_level	Utilisateurs à risque
incidents	id, incident_id, timestamp, title, severity, status, assigned_to, entities, raw_json	TEXT/INT	incident_id (UNIQUE), severity, status	Incidents Defender
audit_logs	id, event_id, timestamp, user_principal, operation, target, result, raw_json	TEXT/INT	event_id (UNIQUE), operation, timestamp	Unified Audit Log
truth_list	id, user_principal, display_name, department, added_date, is_active	TEXT/INT	user_principal (UNIQUE)	Liste de vérité users
new_user_alerts	id, user_principal, first_seen, source_type, status, reviewed_by, reviewed_date	TEXT/INT	user_principal, status	Alertes nouveaux users
ingestion_logs	id, filename, upload_date, lines_total, lines_added, lines_duplicate, status	TEXT/INT	upload_date	Trace des ingestions
🗄️ DB_ARCHIVE (siem_archive.db)
Table	Colonnes	Type	Index	Description
archived_signins	(mêmes colonnes que signins)	TEXT/INT	timestamp, user_principal	SignIns archivés
archived_risky_users	(mêmes colonnes que risky_users)	TEXT/INT	timestamp, user_principal	Risky Users archivés
archived_incidents	(mêmes colonnes que incidents)	TEXT/INT	timestamp, incident_id	Incidents archivés
archived_audit_logs	(mêmes colonnes que audit_logs)	TEXT/INT	timestamp, operation	Audit Logs archivés
backup_manifest	id, backup_filename, backup_date, record_count, md5_checksum, status	TEXT/INT	backup_date	Trace des backups
🗄️ DB_CONFIG (siem_config.db)
Table	Colonnes	Type	Description
settings	key, value, updated_date	TEXT	Configuration application
users	id, username, password_hash, role, created_date	TEXT	Authentification UI
audit_trail	id, timestamp, user, action, details	TEXT	Logs d'activité application
3️⃣ API Endpoints Specification
🔌 Base URL : http://localhost:5000/api/v1
Endpoint	Method	Auth	Description	Payload	Response
/auth/login	POST	❌	Authentification	{username, password}	{token, expires}
/auth/logout	POST	✅	Déconnexion	-	{status}
/ingest/upload	POST	✅	Upload fichier logs	multipart/form-data	{lines_added, duplicates, errors}
/ingest/truth-list	POST	✅	Upload liste vérité	multipart/form-data	{users_imported}
/ingest/status	GET	✅	Statut dernière ingestion	-	{last_upload, status}
/query/signins	GET	✅	Rechercher SignIns	?from=&to=&user=&status=	[{...}]
/query/risky	GET	✅	Rechercher Risky Users	?from=&to=&level=	[{...}]
/query/incidents	GET	✅	Rechercher Incidents	?from=&to=&severity=	[{...}]
/query/audit	GET	✅	Rechercher Audit Logs	?from=&to=&operation=	[{...}]
/alerts/new-users	GET	✅	Liste nouveaux users	?status=pending	[{user, first_seen}]
/alerts/approve	POST	✅	Approuver user	{user_principal, action}	{status}
/archive/list	GET	✅	Liste backups disponibles	-	[{filename, date, md5}]
/archive/read	POST	✅	Lire backup sans ingestion	{filename}	[{...}]
/archive/backup	POST	✅	Créer backup manuel	-	{filename, md5}
/dashboard/kpi	GET	✅	KPI pour dashboard	?days=30	{total_events, risky, incidents, new_users}
/dashboard/trends	GET	✅	Tendances temporelles	?metric=signins&days=90	[{date, count}]
/system/health	GET	✅	Santé application	-	{db_size, last_backup, uptime}
4️⃣ Formats JSON
📥 Format d'Ingestion (SignIns)
{
  "source_type": "signins",
  "export_date": "2026-01-15",
  "records": [
    {
      "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "timestamp": "2026-01-15T08:30:00Z",
      "user_principal": "user@domain.com",
      "ip_address": "192.168.1.100",
      "location": {
        "city": "Paris",
        "country": "France"
      },
      "status": "success",
      "failure_reason": null,
      "mfa_status": "mfa_completed",
      "app_name": "Office365",
      "client_app": "Browser"
    }
  ]
}
📥 Format d'Ingestion (Risky Users)
{
  "source_type": "risky_users",
  "export_date": "2026-01-15",
  "records": [
    {
      "event_id": "r1s2k3y4-u5s6-7890-risk-user123456789",
      "timestamp": "2026-01-15T10:00:00Z",
      "user_principal": "user@domain.com",
      "risk_level": "high",
      "risk_state": "atRisk",
      "detection_type": "anomalous_token",
      "details": "Token leaked to public repo"
    }
  ]
}
📦 Format Backup Archive (ZIP contenant JSON)
archive_20260115.zip
├── data.json           (tous les records archivés)
├── manifest.json       (métadonnées du backup)
└── checksum.md5        (empreinte pour intégrité)
manifest.json :

{
  "backup_id": "bkp_20260115_083000",
  "created_date": "2026-01-15T08:30:00Z",
  "source_period": {
    "from": "2025-10-17",
    "to": "2026-01-15"
  },
  "record_counts": {
    "signins": 45000,
    "risky_users": 12,
    "incidents": 34,
    "audit_logs": 8500
  },
  "md5_checksum": "a1b2c3d4e5f6g7h8i9j0"
}
5️⃣ Data Lifecycle Manager
🔄 Cycle de Vie Automatisé
# Pseudo-code du Lifecycle Manager (exécuté quotidiennement à 02:00)

def daily_lifecycle_job():
    # Étape 1 : Déplacer logs > 90 jours de HOT vers ARCHIVE
    cutoff_date = today() - 90 days
    moved_records = db_hot.move_to_archive(cutoff_date)
    
    # Étape 2 : Vérifier si ARCHIVE a atteint 90 jours
    archive_oldest = db_archive.get_oldest_record_date()
    if archive_oldest <= today() - 90 days:
        # Étape 3 : Créer backup JSON ZIP
        backup_file = backup_manager.create_backup()
        
        # Étape 4 : Générer MD5 checksum
        checksum = backup_manager.generate_md5(backup_file)
        
        # Étape 5 : Enregistrer dans manifest
        db_config.record_backup(backup_file, checksum)
        
        # Étape 6 : Nettoyer ARCHIVE
        db_archive.purge_all()
        
        # Étape 7 : Logger l'opération
        audit_log("ARCHIVE_BACKUP_COMPLETED", backup_file)
📊 Tableau de Flux
Étape	Source	Destination	Déclencheur	Fréquence
1	Export M365	Upload UI	Manuel	Quotidien/Hebdo
2	Upload UI	DB_HOT	Automatique	Immédiat
3	DB_HOT (>90j)	DB_ARCHIVE	Job automatique	Quotidien 02:00
4	DB_ARCHIVE (>90j)	JSON ZIP	Job automatique	Quand seuil atteint
5	JSON ZIP	/backups/	Automatique	Immédiat
6	DB_ARCHIVE	Clean	Après backup	Immédiat
7	JSON ZIP	Reader UI	Manuel	À la demande
6️⃣ Stack Technique Détaillée
Composant	Technologie	Version	Justification
Backend	Python + FastAPI	3.11+	Performance, async, documentation auto
Frontend	Vue.js 3 + Vite	3.x	Léger, réactif, écosystème riche
Dashboard	Chart.js + Vue-Chartjs	4.x	Graphiques simples et efficaces
DB Engine	SQLite3	3.40+	Native Python, pas de serveur
DB Encryption	SQLCipher (optionnel)	4.x	Chiffrement transparent
Auth	JWT + bcrypt	-	Stateless, sécurisé
File Handling	Python zipfile + hashlib	-	Native, pas de dépendance
Scheduler	APScheduler	3.x	Jobs récurrents légers
Server	Uvicorn + Gunicorn	-	ASGI performant
OS	Windows 10/11	-	Environnement cible
7️⃣ Sécurité
🔐 Mesures Implémentées
Couche	Mesure	Détails
Authentification	JWT Token	Expiration 30min, refresh token
Passwords	bcrypt hash	Salt + 12 rounds
DB Hot	File permissions	Lecture/écriture admin uniquement
DB Archive	SQLCipher (option)	Chiffrement AES-256
Backups	MD5 Checksum	Vérification intégrité
API	Rate limiting	100 req/min par user
Logs	Audit trail	Toutes actions loguées
Input	Schema validation	Pydantic pour tous les payloads
XSS/CSRF	Headers sécurisés	Content-Security-Policy, SameSite
⚠️ Limites de Sécurité (À Communiquer)
Limite	Impact	Mitigation
Stockage local	Risque vol physique	Chiffrement disque (BitLocker)
Pas de HA	Single point of failure	Backup externe régulier
Auth simple	Pas de MFA UI	Réseau local sécurisé
Logs sensibles	Données personnelles	Accès restreint, purge conforme RGPD
8️⃣ Structure du Projet (Code)
siem-m365/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings
│   │   ├── auth.py              # JWT, bcrypt
│   │   ├── database.py          # SQLite connections
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── hot_db.py
│   │   │   ├── archive_db.py
│   │   │   └── config_db.py
│   │   ├── schemas/             # Pydantic schemas
│   │   │   ├── signins.py
│   │   │   ├── risky_users.py
│   │   │   ├── incidents.py
│   │   │   └── audit_logs.py
│   │   ├── api/                 # Routes
│   │   │   ├── auth.py
│   │   │   ├── ingest.py
│   │   │   ├── query.py
│   │   │   ├── alerts.py
│   │   │   ├── archive.py
│   │   │   └── dashboard.py
│   │   ├── services/            # Business logic
│   │   │   ├── ingestion.py
│   │   │   ├── dedup.py
│   │   │   ├── new_user_detect.py
│   │   │   ├── lifecycle.py
│   │   │   └── backup.py
│   │   └── scheduler/           # APScheduler jobs
│   │       └── daily_jobs.py
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── views/
│   │   │   ├── Dashboard.vue
│   │   │   ├── SignIns.vue
│   │   │   ├── RiskyUsers.vue
│   │   │   ├── Incidents.vue
│   │   │   ├── Alerts.vue
│   │   │   ├── Archives.vue
│   │   │   └── Settings.vue
│   │   ├── components/
│   │   │   ├── KpiCard.vue
│   │   │   ├── DataTable.vue
│   │   │   ├── Chart.vue
│   │   │   └── FileUpload.vue
│   │   ├── stores/              # Pinia state
│   │   └── api/                 # Axios calls
│   ├── package.json
│   └── vite.config.js
├── data/
│   ├── db/                      # SQLite files
│   ├── backups/                 # JSON ZIP backups
│   ├── uploads/                 # Temp upload folder
│   └── config/                  # Config files
├── scripts/
│   ├── export_m365.ps1          # PowerShell export script
│   └── init_db.py               # DB initialization
└── docs/
    ├── api.md
    ├── deployment.md
    └── user_guide.md
9️⃣ Pré-requis Déploiement
Élément	Configuration
OS	Windows 10/11 Pro
Python	3.11+
Node.js	18+ (pour build frontend)
RAM	4GB minimum
Disk	10GB libre minimum
Port	5000 (HTTP), configurable
Firewall	Ouvrir port 5000 en local uniquement
✅ Validation
Cette architecture est prête à être transmise à l'Agent SCRUM MASTER pour le découpage en sprints et stories détaillées.

📦 Prochaine Étape BMAD
👉 Agent suivant : SCRUM MASTER

Prompt à utiliser :

👤 Rôle : Tu es l'AGENT SCRUM MASTER de la méthode BMAD.

📥 Input : Architecture Technique v1.0 (SIEM Manuel M365)

📝 Tâche :
1. Découper le projet en Sprints (2 semaines chacun).
2. Pour chaque Sprint, définir les User Stories à compléter.
3. Estimer la charge (points/story).
4. Définir les critères de DONE par story.
5. Identifier les dépendances et risques par sprint.

⚠️ Règle : Prioriser le MVP fonctionnel (ingestion + dashboard + archive) en Sprint 1-3.

🤖 AGENT SCRUM MASTER BMAD activé.

Note importante prise en compte : Le chiffrement (SQLCipher + BitLocker + Backups) passe de SHOULD à MUST. Impact direct sur Sprint 1 et 2.

📋 SPRINT PLAN — SIEM Manuel M365
Métadonnées	Valeur
Projet	SIEM Manuel M365
Méthode	Scrum (Sprints 2 semaines)
Baseline	Architecture v1.0 + PRD v2.0
Équipe	1 Dev Fullstack + 1 QA (partiel)
Contrainte	Chiffrement OBLIGATOIRE (DB, Backups, Disque)
🗓️ ROADMAP GLOBALE (6 Sprints)
Sprint	Durée	Focus	Objectif Principal
S1	2 sem	Socle Sécurisé	Setup projet + DB chiffrée + Auth
S2	2 sem	Ingestion Core	Upload + Dédup + Truth List
S3	2 sem	Dashboard IT	Query + Visualisation + Alertes
S4	2 sem	Dashboard Direction	KPIs + Tendances + Exports
S5	2 sem	Archive & Backup	Lifecycle + JSON ZIP + Reader
S6	2 sem	Hardening & Recette	Tests QA + Docs + Déploiement
🏃 SPRINT 1 — Socle Sécurisé (Fondations)
Objectif : Environnement de dev opérationnel avec sécurité de base implémentée.

ID	User Story	Points	Critères de DONE	Dépendances
S1-ST1	Setup projet (repo, structure, CI/CD local)	3	Repo Git créé, structure dossiers validée, README à jour	Aucune
S1-ST2	Configuration SQLite + SQLCipher (chiffrement DB HOT)	5	DB créée, chiffrement AES-256 actif, tests lecture/écriture	S1-ST1
S1-ST3	Module d'authentification (JWT + bcrypt)	5	Login/Logout fonctionnel, token expire 30min, password hashé	S1-ST1
S1-ST4	Gestion des rôles (Admin vs Viewer)	3	2 rôles créés, permissions vérifiées par endpoint	S1-ST3
S1-ST5	Audit Trail (logs d'activité application)	3	Toutes actions auth loguées dans DB_CONFIG	S1-ST2, S1-ST3
S1-ST6	Configuration BitLocker (doc + script)	2	Guide rédigé, script vérification statut BitLocker	Aucune
📊 Total Points : 21 | Capacité Équipe : 24 points

⚠️ Risques Sprint 1
Risque	Impact	Mitigation
SQLCipher compatibilité Windows	Bloquant	Tester dès J1, alternative : chiffrement applicatif
Complexité auth JWT	Moyen	Utiliser lib éprouvée (PyJWT)
Performance DB chiffrée	Moyen	Benchmark sur 10k lignes dès S1
✅ Definition of DONE (Sprint 1)
 Code versionné et tagué v0.1.0
 DB HOT chiffrée et testée
 Auth fonctionnelle avec 2 comptes test
 Audit trail actif
 Documentation BitLocker fournie
🏃 SPRINT 2 — Ingestion Core
Objectif : Capacité à importer des logs M365 avec déduplication et détection nouveaux users.

ID	User Story	Points	Critères de DONE	Dépendances
S2-ST1	Endpoint upload fichier (JSON/CSV)	5	Upload via UI, validation schema, erreur claire si invalide	S1-ST3
S2-ST2	Parsing SignIns (JSON schema)	5	100% des champs mappés, raw_json conservé	S2-ST1
S2-ST3	Parsing Risky Users + Incidents	5	2 sources supplémentaires supportées	S2-ST1
S2-ST4	Parsing Unified Audit Log	5	UAL supporté avec mapping opérations clés	S2-ST1
S2-ST5	Logique de déduplication (event_id + timestamp)	5	0 doublon après 2 imports identiques, log rejet	S2-ST2 à S2-ST4
S2-ST6	Upload Liste de Vérité	3	JSON/CSV importé, versioning, date MAJ visible	S1-ST3
S2-ST7	Détection Nouveaux Users (auto-flag)	5	Alert créée si user ∉ Truth List, visible dans UI	S2-ST2, S2-ST6
S2-ST8	Ingestion Logs (traçabilité)	3	Tableau historique des imports dans UI	S2-ST1
📊 Total Points : 36 | Capacité Équipe : 24 points → Débordement, reporter S2-ST4 (UAL) en S3

🔄 Ajustement Sprint 2
À garder	À reporter S3
S2-ST1 à S2-ST3, S2-ST5 à S2-ST8	S2-ST4 (Unified Audit Log)
📊 Total Ajusté : 31 points → Encore serré, prioriser S2-ST1/2/5/6/7

⚠️ Risques Sprint 2
Risque	Impact	Mitigation
Schema M365 variable	Moyen	Validation Pydantic stricte, logs d'erreur détaillés
Performance dédup sur gros fichiers	Moyen	Index DB optimisés, batch insertion
Format Truth List ambigu	Faible	Template JSON fourni avec la doc
✅ Definition of DONE (Sprint 2)
 Upload SignIns + Risky fonctionnel
 Déduplication vérifiée (test avec doublons)
 Truth List importée
 Alertes Nouveaux Users générées
 UAL reporté en Sprint 3
🏃 SPRINT 3 — Dashboard IT & UAL
Objectif : Interface de consultation des logs + support Unified Audit Log.

ID	User Story	Points	Critères de DONE	Dépendances
S3-ST1	Endpoint query SignIns (filtres)	5	Filtres : date, user, status, IP. Pagination active	S2-ST2
S3-ST2	Endpoint query Risky + Incidents	5	Filtres : date, level, severity. Pagination active	S2-ST3
S3-ST3	Intégration Unified Audit Log (parsing)	5	Champs mappés, requêtable comme les autres	S2-ST4 (reporté)
S3-ST4	UI Tableau de logs (DataGrid)	8	Tri, filtres, pagination, export CSV ligne courante	S3-ST1 à S3-ST3
S3-ST5	UI Alertes Nouveaux Users (approve/reject)	5	Liste pending, boutons action, statut mis à jour	S2-ST7
S3-ST6	Chiffrement Backups (ZIP AES-256)	5	Backup chiffré avec password config, MD5 généré	S1-ST2
S3-ST7	UI Page Archives (liste backups)	3	Tableau des backups avec date, taille, MD5	S3-ST6
📊 Total Points : 36 | Capacité Équipe : 24 points → Reporter S3-ST3 (UAL) si nécessaire

🔄 Ajustement Sprint 3
À garder	À reporter S4
S3-ST1, S3-ST2, S3-ST4, S3-ST5, S3-ST6, S3-ST7	S3-ST3 (UAL complet)
📊 Total Ajusté : 31 points → S3-ST3 partiellement inclus

⚠️ Risques Sprint 3
Risque	Impact	Mitigation
Performance DataGrid (10k+ lignes)	Moyen	Virtual scrolling, server-side pagination
Chiffrement backup lent	Faible	Compression avant chiffrement, async job
UX approbation users	Faible	Mockup validé avant dev
✅ Definition of DONE (Sprint 3)
 Query SignIns + Risky + Incidents fonctionnel
 UI DataGrid avec filtres et pagination
 Workflow approbation Nouveaux Users complet
 Backups chiffrés créables manuellement
 UAL en cours (finalisation S4)
🏃 SPRINT 4 — Dashboard Direction & UAL Final
Objectif : Vue synthétique pour la Direction + finalisation UAL.

ID	User Story	Points	Critères de DONE	Dépendances
S4-ST1	Endpoint KPI (total events, risks, incidents)	5	Agrégats calculés, période paramétrable	S3-ST1 à S3-ST2
S4-ST2	Endpoint Tendances (timeseries)	5	Data points par jour/semaine, format chart-ready	S3-ST1 à S3-ST2
S4-ST3	UI Dashboard Direction (KPI Cards)	5	6 cartes KPI, couleurs statut, refresh auto	S4-ST1
S4-ST4	UI Dashboard Tendances (Graphiques)	5	2 graphiques min (SignIns/jour, Incidents/semaine)	S4-ST2
S4-ST5	Finalisation Unified Audit Log	5	Toutes opérations critiques mappées, UI dédiée	S3-ST3
S4-ST6	Export PDF (rapport direction)	5	PDF A4, logo, période, KPIs, tableau résumé	S4-ST3, S4-ST4
S4-ST7	UI Reader JSON (lecture backup sans ingestion)	8	Upload ZIP, lecture directe, recherche, pas d'écriture DB	S3-ST6
📊 Total Points : 38 | Capacité Équipe : 24 points → Reporter S4-ST6 (PDF) en S6

🔄 Ajustement Sprint 4
À garder	À reporter S6
S4-ST1 à S4-ST5, S4-ST7	S4-ST6 (Export PDF)
📊 Total Ajusté : 33 points → Encore serré, S4-ST7 peut être partiel

⚠️ Risques Sprint 4
Risque	Impact	Mitigation
Performance agrégats KPI	Moyen	Index DB, cache 5min
Lecture gros backup JSON	Moyen	Streaming, pagination dans le reader
UAL operations mapping	Faible	Documentation Microsoft officielle
✅ Definition of DONE (Sprint 4)
 Dashboard Direction avec 6 KPIs + 2 graphiques
 UAL fully fonctionnel
 Reader JSON opérationnel (lecture seule)
 Export PDF reporté en S6
🏃 SPRINT 5 — Archive & Lifecycle Automatisé
Objectif : Automatisation du cycle de vie des données (Hot → Archive → Backup).

ID	User Story	Points	Critères de DONE	Dépendances
S5-ST1	Job automatique déplacement HOT→ARCHIVE (>90j)	5	APScheduler configuré, exécution 02:00, logs	S1-ST2
S5-ST2	DB Archive chiffrée (SQLCipher)	5	Même chiffrement que DB HOT, clés séparées	S1-ST2
S5-ST3	Trigger backup quand Archive atteint 90j	5	Détection automatique, notification UI	S5-ST1
S5-ST4	Cleanup Archive après backup réussi	3	Table vidée, log de cleanup, rollback si échec	S5-ST3
S5-ST5	UI Section Archive Management	5	Vue des jobs, historique backups, trigger manuel	S5-ST1 à S5-ST4
S5-ST6	Notification alertes (UI banner)	3	Banner si backup échoué ou archive pleine	S5-ST3
S5-ST7	Tests de restauration depuis backup	5	Procédure testée, doc de restore rédigée	S3-ST6, S4-ST7
📊 Total Points : 31 | Capacité Équipe : 24 points → Reporter S5-ST6 en S6

🔄 Ajustement Sprint 5
À garder	À reporter S6
S5-ST1 à S5-ST5, S5-ST7	S5-ST6 (Notifications UI)
📊 Total Ajusté : 28 points → Faisable avec focus

⚠️ Risques Sprint 5
Risque	Impact	Mitigation
Job automatique échoue	Critique	Logging détaillé, alerte log fichier
Perte données lors cleanup	Critique	Backup validé AVANT cleanup, transactionnelle
Conflit de clés chiffrement	Moyen	Documentation claire des key locations
✅ Definition of DONE (Sprint 5)
 Job quotidien HOT→ARCHIVE fonctionnel
 Backup automatique déclenché à 90j archive
 Cleanup Archive post-backup validé
 Tests de restauration documentés et passés
 Notifications reportées en S6
🏃 SPRINT 6 — Hardening, Recette & Déploiement
Objectif : Finalisation, tests QA, documentation et package de déploiement.

ID	User Story	Points	Critères de DONE	Dépendances
S6-ST1	Export PDF (rapport direction)	5	PDF généré, formaté, avec logo et KPIs	S4-ST3, S4-ST4
S6-ST2	Notifications UI (backup échec, archive pleine)	3	Banner visible, historique notifications	S5-ST6
S6-ST3	Tests QA complets (ingestion, query, archive)	8	Plan de test exécuté, 0 bug critique, rapport QA	Tous sprints
S6-ST4	Performance tuning (benchmark 180 users/90j)	5	Requêtes <2s, ingestion <30s/10k lignes	S3-ST4, S5-ST1
S6-ST5	Documentation utilisateur (guide + vidéos)	5	PDF user guide, 3 vidéos tutoriels (export, ingest, review)	Toutes UI
S6-ST6	Package déploiement (installer Windows)	5	Script d'install, config auto, service Windows optionnel	S1-ST1
S6-ST7	Formation équipe IT (handover)	3	Session 2h, Q&R, accès docs	S6-ST5
S6-ST8	Chiffrement BitLocker vérifié	2	Script de vérification exécuté, rapport	S1-ST6
📊 Total Points : 36 | Capacité Équipe : 24 points → Reporter S6-ST7 (formation) post-projet

🔄 Ajustement Sprint 6
À garder	À reporter Post-Projet
S6-ST1 à S6-ST6, S6-ST8	S6-ST7 (Formation)
📊 Total Ajusté : 33 points → Dernier sprint, buffer nécessaire

⚠️ Risques Sprint 6
Risque	Impact	Mitigation
Bugs découverte tardive	Critique	Buffer 3 jours dans le sprint
Performance insuffisante	Moyen	Tuning priorisé, index additionnels
Documentation incomplète	Faible	Template imposé, review par Analyste
✅ Definition of DONE (Sprint 6)
 Export PDF fonctionnel
 Notifications UI actives
 QA rapporté (0 bug critique)
 Performance validée (benchmarks)
 Documentation complète
 Package déploiement prêt
 BitLocker vérifié
 PROJET LIVRABLE
📊 RÉCAPITULATIF DES POINTS PAR SPRINT
Sprint	Points Planifiés	Points Ajustés	Capacité	Statut
S1	21	21	24	✅ Faisable
S2	36	31	24	⚠️ Serré (UAL reporté)
S3	36	31	24	⚠️ Serré (UAL partiel)
S4	38	33	24	⚠️ Serré (PDF reporté)
S5	31	28	24	⚠️ Serré (Notif reporté)
S6	36	33	24	⚠️ Serré (Formation post)
TOTAL	198	177	144	⚠️ +33 points de dépassement
🚨 ALERTE CAPACITÉ
Problème identifié : 177 points estimés pour 144 points de capacité (6 sprints × 24 points).

Options de Résolution
Option	Description	Impact
A	Ajouter 1 Dev sur S2-S4	+72 points capacité, coût supplémentaire
B	Étendre à 7 sprints (+2 semaines)	+24 points capacité, livraison retardée 2 sem
C	Réduire scope (drop UAL ou PDF)	-20 points, fonctionnalité en moins
D	Augmenter vélocité équipe (28 pts/sprint)	+24 points, risque burnout
🎯 Recommandation Scrum Master
Option B + C combinée :

Étendre à 7 sprints (14 semaines au lieu de 12)
Reporter Export PDF en version 1.1 (post-projet)
Nouveau total : 157 points pour 168 capacité ✅
📦 Prochaine Étape BMAD
👉 Agent suivant : DÉVELOPPEUR (pour Sprint 1)

Prompt à utiliser :

👤 Rôle : Tu es l'AGENT DÉVELOPPEUR de la méthode BMAD.

📥 Input : 
- Architecture Technique v1.0
- Sprint 1 détaillé (Socle Sécurisé)
- Contrainte : Chiffrement OBLIGATOIRE (SQLCipher)

📝 Tâche Sprint 1 :
1. Créer la structure du projet (backend/frontend/data)
2. Implémenter DB SQLite + SQLCipher (chiffrement AES-256)
3. Créer les modèles (Auth, Audit Trail, Settings)
4. Implémenter Auth (JWT + bcrypt) avec rôles Admin/Viewer
5. Configurer APScheduler pour jobs futurs
6. Écrire tests unitaires pour Auth + DB

⚠️ Règle : 
- Code production-ready, commenté, sécurisé
- Pas de hardcoded secrets (utiliser .env)
- Chiffrement NON NÉGOCIABLE
