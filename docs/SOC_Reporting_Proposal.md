# Proposition: SOC Reporting avec Analyse MITRE

## 1. Contexte

Exploiter les données d'authentification Microsoft 365 pour créer un **tableau de bord SOC** avec :
- Localisation (City, Country)
- Adresse IP	source
- Cartographie MITRE ATT&CK pour identifier les techniques d'attaque

---

## 2. Données disponibles dans SignIns

| Champ | Description | Usage SOC |
|-------|-------------|---------|
| `ip_address` | IP source de connexion | Géolocalisation, réputation IP |
| `location_city` | Ville de connexion | Heatmap géographique |
| `location_country` | Pays de connexion | Filtrage géographique |
| `user_agent` | Navigateur/app | Détection anomalie |
| `app_name` | Application access | Comportement anormal |
| `status` | Succès/Échec | Taux d'échec suspect |
| `timestamp` | Date/heure | Corrélation temporelle |

---

## 3. Proposition KPIs SOC

### 🎯 3.1 KPI de Détection

| KPI | Formule | Source |
|-----|--------|-------|
| **Taux de couverture** | Logs reçus / Logs attendus | Ingestion logs |
| **Taux détection automatique** | Alertes auto / Total incidents | Alert service |
| **Faux positifs** | Alertes valides × 100 / Total alertes | Alert service |
| **Alertes critiques** | Count status=high-risk | Risky users |
| **IP suspectes externes** | IPs hors pays autorisés | Géolocalisation |

### ⚡ 3.2 KPI de Réponse

| KPI | Formule | Source |
|-----|---------|-------|
| **MTTD** (Mean Time To Detect) | Avg(temps_détection - timestamp) | SignIns failed |
| **MTTA** (Mean Time To Acknowledge) | Avg(temps_pris_en_charge - timestamp) | Alerts |
| **MTTR** (Mean Time To Respond) | Avg(temps_résolution - timestamp) | Incidents |
| **Taux résolution** | Incidents clos × 100 / Total | Incidents |
| **Taux escalation** | Incidents escaladés × 100 / Total | Incidents |

### 🛡️ 3.3 KPI de Posture de Sécurité

| KPI | Description |
|-----|-------------|
| **Score de sécurité global** (0-100) | Combinaison KPIs |
| **Taux connexions hors pays** | Country != FR (ou liste autorisée) |
| **Taux connexions suspectes** | IP connu malveillant (feed TI) |
| **Taux Shadow IT** | Nouvelles apps non autorisées |

### 📊 3.4 KPI Opérationnels

| KPI | Description |
|-----|-------------|
| **Charge analyste** | Alertes traitée / analyste / jour |
| **Alertes en attente** | Queue size |
| **Taux automatisation** | Alerts auto-close × 100 / Total |
| **Disponibilité SIEM** | Uptime % |

### 🔍 3.5 KPI Threat Intelligence

| KPI | Description |
|-----|-------------|
| **IPs malveillantes détectées** | Par rapport feed TI |
| **Pays à risque** | Connexions depuis pays haute menace |
| **Tentatives bloquées** | Status=failed avec motif suspect |

### 🧩 3.6 Cartographie MITRE ATT&CK

 Mapper les activités detects aux techniques MITRE :

| Activité Détectée | Technique MITRE | ID |
|------------------|----------------|-----|
| Échec mot de passe répété | Credential Stuffing | T1110 |
| Connexion depuis nouveau pays | Remote Services | T1021 |
| Connexion VPN absent | Exfiltration Proxy | T1041 |
| Connexion horaires atypiques | System Services | T1569 |
| Multiples échecs | Brute Force | T1110 |
| Connexion anomalie | Valid Accounts | T1078 |

---

## 4. Architecture proposée

```
┌─────────────────┐
│   SignIns JSON   │
└────────┬────────┘
         │
    ┌────▼────┐
    │Parser  │ ───► Extraction IP, City, Country
    └────┬────┘
         │
┌──────���─▼────────┐     ┌──────────────┐
│  Géolocalisation│ ───►│ IPs Pays    │
│  (IP → Country) │     │ Frequence  │
└────────┬────────┘     └──────────────┘
         │
┌────────▼────────┐     ┌──────────────┐
│  Analytics SOC │ ───►│ KPIs SOC     │
│  MITRE Mapper  │     │ Dashboards   │
└────────┬────────┘     └──────────────┘
         │
    ┌────▼────┐
    │ Dashboard│
    │ SOC     │
    └─────────┘
```

---

## 5. Dépendances techniques

1. **Géolocalisation IP** : Library `geoip2` ou API externe (IpApi, ipstack)
2. **Feed Threat Intelligence** : APIFeeds (AbuseIPDB, OTX AlienVault)
3. **Mapping MITRE** : Table de correspondance statique

---

## 6. Implémentation suggérée

### Phase 1: Métriques de base
- KPIs détection depuis SignIns (connexions par pays, par ville, taux échec)
-KPIs réponse depuis Incidents (MTTD, MTTR)

### Phase 2: Threat Intelligence
-Intégration feed IPs malveillantes
-Géolocalisation automatique

### Phase 3: Cartographie MITRE
-Mapping activités vers techniques MITRE
-Dashboard visuel

---

## 7. Questions en suspens

1. ✅Avez-vous un feed Threat Intelligence?
2. ✅Liste des pays autorisés?
3. ✅Seuils desider pour les alertes ?
4. ✅Intégration avec un SOAR ?

---

**Prochaine étape**: Valider cette proposition puis implémenter Phase 1 ?