# Trust PWS — Prototype scientifique

Prototype de démonstration du mémoire :

**Construction d’un cadre reproductible pour l’évaluation de la confiance dans les données produites par une station météorologique personnelle low-cost**

React affiche et orchestre. Les calculs scientifiques restent dans l’API FastAPI (exports du pipeline notebooks + upload / IoT).

## Prérequis

- Node.js 20+
- Python 3.11+
- Données déjà produites sous `notebook/notebook/data/processed/` (pour le tableau de bord corpus)
- Pour IoT seul (simulation / Arduino) : les données corpus ne sont pas obligatoires

## Démarrage (important)

> **Toujours lancer l’API depuis le dossier `App/api`**, pas depuis la racine du dépôt.  
> Sinon : `ModuleNotFoundError: No module named 'app'`.

Les chemins ci-dessous partent de la **racine du dépôt** `TRUST-PWS/`.

### 1. API FastAPI — Terminal 1

**Windows (PowerShell)**

```powershell
cd App\api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Usage local (UI sur le même PC)
python -m uvicorn app.main:app --reload --port 8000

# Usage IoT / Arduino sur le WiFi (écoute réseau)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Linux / macOS**

```bash
cd App/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Vérifications :
- Santé : http://127.0.0.1:8000/health  
- Docs : http://127.0.0.1:8000/docs  

Vous devez voir dans le terminal quelque chose comme :

```text
Uvicorn running on http://0.0.0.0:8000
Application startup complete.
```

### 2. Frontend React — Terminal 2

```powershell
cd App
npm install
npm run dev
```

UI : **http://localhost:5173**  
Le proxy Vite envoie `/api` → `http://127.0.0.1:8000`.

## Écrans

| Route | Rôle |
|---|---|
| `/` | Tableau de bord (corpus mémoire) |
| `/import` | Upload CSV/JSON + contrôle de format + évaluation |
| `/iot` | Flux Arduino / ESP32 ou simulation sans matériel |
| `/visualisation` | Séries T/H/P |
| `/evaluation` | Étapes du cadre |
| `/anomalies` | Observations suspectes |
| `/score` | Score + radar dimensions |
| `/historique` | Synthèse par station |

## Import fichier

Page **Import** (`/import`) :

1. Upload CSV/JSON  
2. Vérification du format via l’API  
3. Évaluation QC + confiance  
4. Option de retirer les valeurs suspectes + export normalisé  

Formats acceptés :
- **long** : `timestamp, value, phenomenon|variable [, unit, station_id]`
- **large** : `timestamp, temperature, humidity, pressure`

Exemple : [`api/sample_station.csv`](api/sample_station.csv)

## IoT / Arduino

Page UI : **http://localhost:5173/iot**

1. API avec `--host 0.0.0.0` (voir ci-dessus), depuis **`App/api`**
2. Même WiFi que l’ESP32
3. Sketch : [`arduino/trust_pws_esp32.ino`](arduino/trust_pws_esp32.ino)  
4. Guide : [`arduino/README.md`](arduino/README.md)

Sans matériel : bouton **Simuler sans matériel** sur `/iot`.

```http
POST http://IP_DU_PC:8000/iot/ingest
Content-Type: application/json

{"device_id":"esp32-salon","temperature":22.5,"humidity":55.0,"pressure":1013.2}
```

## Erreurs fréquentes

| Message / symptôme | Cause | Solution |
|---|---|---|
| `No module named 'app'` | Commande lancée hors de `App/api` (souvent depuis la racine) | `cd App\api` puis relancer uvicorn |
| `No module named 'fastapi'` | Mauvais Python / venv non activé | `.\.venv\Scripts\Activate.ps1` puis `pip install -r requirements.txt` |
| UI qui ne charge pas les données | API arrêtée ou mauvais port | Vérifier http://127.0.0.1:8000/health |
| ESP32 n’atteint pas l’API | `--host 127.0.0.1` ou mauvaise IP | Utiliser `--host 0.0.0.0` et l’IP LAN du PC (pas `127.0.0.1` dans le sketch) |

## Architecture

- `src/pages` : écrans  
- `src/services` : client Axios (pas de logique QC dans React)  
- `api/app` : FastAPI + corpus + upload + IoT  
- `arduino/` : sketch ESP32  

Périmètre variables : **température, humidité, pression**.
