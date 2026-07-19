# TRUST-PWS

**Construction d’un cadre reproductible pour l’évaluation de la confiance dans les données produites par une station météorologique personnelle low-cost**

Ce dépôt fournit la **méthode** (notebooks + scripts) et un **prototype** (React + FastAPI).  
Les **datasets ne sont pas dans Git** (~1 Go+) : vous les produisez vous-même, étape par étape.

Périmètre : **température, humidité, pression** (T/H/P) — corpus openSenseMap outdoor.  
Le score de confiance est **relatif** (pas une certification métrologique).

---

## Vue d’ensemble du parcours

```text
0. Cloner + environnement Python
1. Acquisition des données          → data/raw/ + data/metadata/
2. (Optionnel) Visualisation        → data/readable/ + figures exploration
3. Contrôle qualité (QC)            → data/processed/*qc*
4. Score de confiance + FFP         → data/processed/*trust*
5. Tableaux & figures mémoire       → reports/tables/ + reports/figures/
6. (Optionnel) Lancer le prototype  → App UI + API
```

Guide détaillé côté notebooks : [`notebook/notebook/00_PIPELINE_PAS_A_PAS.md`](notebook/notebook/00_PIPELINE_PAS_A_PAS.md)

---

## Structure du dépôt

```text
TRUST-PWS/
├── README.md                          ← ce guide
├── notebook/notebook/                 ← pipeline scientifique
│   ├── 00_PIPELINE_PAS_A_PAS.md
│   ├── Notebook_0_...ipynb            ← orchestrateur (recommandé)
│   ├── Notebook_1_... → Notebook_4_...
│   ├── download_opensensemap_thp.py
│   ├── implement_trust_framework.py
│   ├── requirements.txt
│   ├── data/                          ← vide au clone (.gitkeep)
│   └── reports/                       ← vide au clone (.gitkeep)
├── App/                               ← prototype React + FastAPI
└── document/                          ← rédaction LaTeX
```

---

## Étape 0 — Préparer l’environnement

### Prérequis

| Outil | Version conseillée | Usage |
|---|---|---|
| Python | 3.11+ | notebooks + scripts + API |
| Node.js | 20+ | prototype UI uniquement (étape 6) |
| Git | — | clonage |
| Jupyter / VS Code | — | exécuter les notebooks |
| Internet | — | téléchargement openSenseMap (étape 1) |

### Cloner le dépôt

```bash
git clone https://github.com/Strategiemilambopaul/TRUST-PWS.git
cd TRUST-PWS
```

### Créer un environnement Python (recommandé)

**Windows (PowerShell)**

```powershell
cd notebook\notebook
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS**

```bash
cd notebook/notebook
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Puis ouvrir Jupyter depuis ce dossier (environnement activé) :

```bash
jupyter notebook
# ou : code .   (VS Code + extension Jupyter)
```

> **Temps / disque** : l’acquisition peut prendre du temps (API openSenseMap) et produire ~1 Go de CSV. Prévoir plusieurs Go libres.

---

## Étape 1 — Acquérir le corpus (données brutes)

**Objectif :** obtenir les mesures T/H/P au format long.

### Option A — Orchestrateur (recommandée)

1. Ouvrir `notebook/notebook/Notebook_0_Executer_pipeline_pas_a_pas.ipynb`
2. Exécuter les cellules **dans l’ordre** (haut → bas)
3. Laisser l’étape d’acquisition se terminer

### Option B — Notebook 1 seul

1. Ouvrir `Notebook_1_Acquisition_dataset.ipynb`
2. Exécuter toutes les cellules

### Option C — Script (gros volume / reprise)

```bash
cd notebook/notebook
python download_opensensemap_thp.py
```

### ✅ Résultat attendu (étape 1)

Vérifier que ces fichiers existent :

- [ ] `data/raw/opensensemap_raw_long_active_50.csv`
- [ ] `data/metadata/stations_selectionnees_actives.csv` (ou équivalent stations)

Si ces fichiers sont absents, **ne passez pas à l’étape 3** : relancez l’acquisition.

---

## Étape 2 — Visualisation (optionnelle)

**Objectif :** explorer les séries T/H/P de façon lisible.

1. Ouvrir `Notebook_1bis_Visualisation_lisible.ipynb`
2. Exécuter les cellules

### ✅ Résultat attendu (étape 2)

- [ ] Aperçus sous `data/readable/` (si produit)
- [ ] Figures éventuelles sous `reports/figures_exploration/`

Cette étape n’est **pas bloquante** pour le QC.

---

## Étape 3 — Contrôle qualité (QC)

**Objectif :** flagger chaque observation (`valide` / `a_verifier` / `suspecte`).

### Via Notebook 0 ou Notebook 2

1. Continuer `Notebook_0_...` **ou** ouvrir `Notebook_2_Preparation_Controle_Qualite_openSenseMap.ipynb`
2. Exécuter jusqu’aux exports QC

### Via script (robuste)

```bash
cd notebook/notebook
python implement_trust_framework.py
```

> Le script enchaîne QC **et** confiance (étapes 3 + 4). Utile si les notebooks sont trop lourds.

### ✅ Résultat attendu (étape 3)

- [ ] `data/processed/opensensemap_measurements_qc_flagged.csv` (ou `.parquet`)
- [ ] `data/processed/opensensemap_qc_metrics_station_variable.csv`
- [ ] Paramètres éventuels : `opensensemap_qc_parameters.json`

Vous devez pouvoir distinguer les statuts QC au niveau **observation**.

---

## Étape 4 — Score de confiance et fit-for-purpose

**Objectif :** calculer le score multi-dimensions et classer les séries / stations.

1. Continuer `Notebook_0_...` **ou** ouvrir `Notebook_3_Score_confiance_fit_for_purpose.ipynb`
2. Exécuter toutes les cellules  
   *(déjà fait si vous avez lancé `implement_trust_framework.py`)*

### ✅ Résultat attendu (étape 4)

- [ ] `data/processed/opensensemap_trust_scores_series.csv`
- [ ] `data/processed/opensensemap_trust_scores_stations.csv`
- [ ] `data/processed/opensensemap_fit_for_purpose_summary.csv`
- [ ] `data/processed/opensensemap_trust_parameters.json` (si exporté)

Ne pas confondre :

| Notion | Niveau | Produit à l’étape |
|---|---|---|
| `valide` / `a_verifier` / `suspecte` | observation | 3 |
| `trust_score` + classes FFP | série / station | 4 |

---

## Étape 5 — Tableaux et figures pour le mémoire

**Objectif :** générer les exports de présentation.

1. Ouvrir `Notebook_4_Resultats_memoire.ipynb` (ou finir `Notebook_0_...`)
2. Exécuter les cellules

### ✅ Résultat attendu (étape 5)

- [ ] Fichiers sous `reports/tables/`
- [ ] Figures sous `reports/figures/` (ex. `fig2b_qc_status_*.png`, figures FFP)
- [ ] `reports/manifest_memoires_exports.csv` (si prévu par le notebook)

À ce stade, le **cadre empirique du mémoire** est reproductible localement.

---

## Étape 6 — Lancer le prototype (optionnel)

Prérequis : au minimum les exports de l’**étape 4** dans `notebook/notebook/data/processed/`.

### 6.1 — API FastAPI

**Terminal 1**

```powershell
cd App\api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Vérifier : http://127.0.0.1:8000/health  
Docs : http://127.0.0.1:8000/docs

### 6.2 — Interface React

**Terminal 2**

```powershell
cd App
npm install
npm run dev
```

Ouvrir : **http://localhost:5173**  
(Le proxy Vite envoie `/api` → `http://127.0.0.1:8000`.)

### 6.3 — Ce que vous pouvez faire dans l’UI

| Page | Rôle |
|---|---|
| Tableau de bord | Synthèse corpus mémoire |
| Import | Upload d’une station perso + contrôle de format |
| Évaluation / Score | QC + confiance (calcul côté API) |
| Anomalies | Observations signalées |
| Export | Dataset normalisé (avec option de retirer les suspectes) |

Fichier d’exemple pour tester l’import : [`App/api/sample_station.csv`](App/api/sample_station.csv)

**Format attendu pour un upload :**

- **long** : `timestamp, value, phenomenon|variable [, unit, station_id]`
- **large** : `timestamp, temperature, humidity, pressure`

### 6.4 — Tester en direct avec Arduino / ESP32 (IoT)

Pour une personne qui veut **tester immédiatement** avec un capteur low-cost :

1. Lancer l’API en écoute sur le réseau local :

```powershell
cd App\api
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Ouvrir l’UI : **http://localhost:5173/iot**
3. Soit :
   - flasher le sketch [`App/arduino/trust_pws_esp32.ino`](App/arduino/trust_pws_esp32.ino) (ESP32 + BME280),  
   - **ou** cliquer **Simuler sans matériel** dans l’UI,
   - **ou** envoyer une mesure manuelle depuis la page.
4. Quand le buffer a assez de points → **Évaluer le flux IoT**

Endpoint Arduino :

```http
POST http://IP_DU_PC:8000/iot/ingest
Content-Type: application/json

{"device_id":"esp32-salon","temperature":22.5,"humidity":55.0,"pressure":1013.2}
```

Guide matériel : [`App/arduino/README.md`](App/arduino/README.md)

---

## En cas de problème

| Symptôme | Piste |
|---|---|
| `FileNotFoundError` sur un CSV processed | Relancer les étapes 1 → 4 dans l’ordre |
| Acquisition très lente / coupures | Reprendre avec `download_opensensemap_thp.py` |
| API : `No module named fastapi` | Activer le `.venv` de `App/api` puis `pip install -r requirements.txt` |
| UI vide / erreurs réseau | Vérifier que l’API tourne sur le port **8000** |
| Notebook 0 « saute » une étape | Les sorties existent déjà ; mettre `FORCE_*=True` dans le notebook pour forcer |

---

## Checklist finale (reproduction complète)

- [ ] Étape 0 : venv + dépendances notebooks
- [ ] Étape 1 : `data/raw/` + métadonnées stations
- [ ] Étape 3 : exports QC dans `data/processed/`
- [ ] Étape 4 : scores confiance + FFP
- [ ] Étape 5 : `reports/tables/` + `reports/figures/`
- [ ] (Optionnel) Étape 6 : API `:8000` + UI `:5173`

---

## Références internes

- Pipeline détaillé : [`notebook/notebook/00_PIPELINE_PAS_A_PAS.md`](notebook/notebook/00_PIPELINE_PAS_A_PAS.md)
- Prototype : [`App/README.md`](App/README.md)
- Rédaction : [`document/Marie_victoria_Redaction.tex`](document/Marie_victoria_Redaction.tex)
