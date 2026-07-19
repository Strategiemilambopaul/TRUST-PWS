# Trust PWS — Prototype scientifique

Prototype de démonstration du mémoire :

**Construction d’un cadre reproductible pour l’évaluation de la confiance dans les données produites par une station météorologique personnelle low-cost**

React affiche et orchestre. Les calculs scientifiques restent dans l’API FastAPI (exports du pipeline notebooks).

## Prérequis

- Node.js 20+
- Python 3.11+
- Données déjà produites sous `notebook/notebook/data/processed/`

## Démarrage

### 1. API

```bash
cd App/api
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Docs OpenAPI : http://127.0.0.1:8000/docs

### 2. Frontend

```bash
cd App
npm install
npm run dev
```

UI : http://127.0.0.1:5173  
Le proxy Vite `/api` → `http://127.0.0.1:8000`.

## Écrans

| Route | Rôle |
|---|---|
| `/` | Tableau de bord |
| `/import` | Import CSV/JSON + aperçu |
| `/visualisation` | Séries T/H/P |
| `/evaluation` | 8 étapes du cadre |
| `/anomalies` | Observations suspectes |
| `/score` | Score + radar dimensions |
| `/historique` | Synthèse par station |

## Import & évaluation d’une station

Page **Import** (`/import`) :

1. Upload CSV/JSON
2. `POST /import/preview` — contrôle de format
3. `POST /evaluate` avec fichier — QC + score de confiance (même logique que `implement_trust_framework.py`)

Formats acceptés :
- **long** : `timestamp, value, phenomenon|variable [, unit, station_id]`
- **large** : `timestamp, temperature, humidity, pressure`

Exemple : `api/sample_station.csv`

## IoT / Arduino

Page UI : `/iot`

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- `POST /iot/ingest` — JSON T/H/P depuis ESP32  
- `POST /iot/simulate` — démo sans matériel  
- Sketch : `arduino/trust_pws_esp32.ino`  
- Guide : `arduino/README.md`

## Architecture

- `src/pages` : écrans
- `src/services` : client Axios (pas de logique QC dans React)
- `src/store` : Zustand (filtres UI)
- `api/app` : FastAPI + corpus mémoire + évaluation d’upload

Périmètre variables : **température, humidité, pression** (pas vent/précipitations dans ce corpus).
