# TRUST-PWS

Cadre reproductible pour l’évaluation de la confiance dans les données produites par une station météorologique personnelle low-cost (T/H/P).

Ce dépôt contient la **méthode** (notebooks, scripts) et le **prototype** (React + FastAPI).  
Les **datasets** ne sont pas versionnés : ils se génèrent pas à pas via le pipeline.

## Structure

```text
notebook/notebook/   # Pipeline mémoire (NB0 → NB4)
App/                 # Prototype scientifique (UI + API)
document/            # Rédaction LaTeX
```

## Prérequis

- Python 3.11+ (3.14 OK avec venv)
- Node.js 20+
- Connexion Internet pour l’acquisition openSenseMap

## Données : installation pas à pas

Les dossiers `data/` et `reports/` sont vides dans Git. Pour les produire :

```bash
cd notebook/notebook
```

1. Ouvrir `00_PIPELINE_PAS_A_PAS.md` (guide)
2. Exécuter `Notebook_0_Executer_pipeline_pas_a_pas.ipynb` cellule par cellule  
   **ou** enchaîner :
   - NB1 acquisition → `data/raw/` + `data/metadata/`
   - NB1bis visualisation (optionnel)
   - NB2 QC → `data/processed/*qc*`
   - NB3 confiance / FFP → `data/processed/*trust*`
   - NB4 résultats → `reports/tables/` + `reports/figures/`

Alternatives scripts (gros volumes) :

```bash
python download_opensensemap_thp.py
python implement_trust_framework.py
```

## Prototype applicatif

Après avoir généré au moins les exports `data/processed/` :

```bash
# API
cd App/api
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# UI (autre terminal)
cd App
npm install
npm run dev
```

- UI : http://localhost:5173  
- API docs : http://127.0.0.1:8000/docs  
- Page **Import** : upload d’une station personnelle + QC/confiance + export normalisé

Exemple de fichier de test : `App/api/sample_station.csv`

## Périmètre scientifique

Variables : **température, humidité, pression** (pas vent / précipitations dans ce corpus).  
Score de confiance **relatif**, non métrologique.

## Licence / usage

Projet de mémoire — reproduction du cadre méthodologique et du prototype de démonstration.
