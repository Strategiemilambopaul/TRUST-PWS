# Pipeline du mémoire — guide unique

**Titre :** Construction d’un cadre reproductible pour l’évaluation de la confiance dans les données produites par une station météorologique personnelle low-cost

**Corpus :** openSenseMap — température, humidité, pression — outdoor

---

## Structure du projet (fichiers utiles)

| Fichier | Rôle |
|---|---|
| `Notebook_0_Executer_pipeline_pas_a_pas.ipynb` | **Orchestrateur** : exécute le pipeline cellule après cellule |
| `Notebook_1_Acquisition_dataset.ipynb` | Méthode + acquisition du corpus |
| `Notebook_1bis_Visualisation_lisible.ipynb` | Exploration T/H/P (optionnel) |
| `Notebook_2_Preparation_Controle_Qualite_openSenseMap.ipynb` | Preuves QC (`valide` / `a_verifier` / `suspecte`) |
| `Notebook_3_Score_confiance_fit_for_purpose.ipynb` | Score de confiance + classes d’usage |
| `Notebook_4_Resultats_memoire.ipynb` | Tableaux & figures pour le mémoire |
| `download_opensensemap_thp.py` | Script acquisition (gros volume / reprise) |
| `implement_trust_framework.py` | Script QC + confiance (gros volume) |

Les notebooks portent la **méthode** du mémoire.  
Les scripts Python sont l’alternative **robuste** pour les gros volumes.

---

## Enchaînement

```text
Notebook 0  (recommandé pour un run complet)
     │
     ├─► 1  Acquisition          → data/raw/ + data/metadata/
     ├─► 1bis Visualisation      → data/readable/ + reports/figures_exploration/  [optionnel]
     ├─► 2  Contrôle qualité     → data/processed/*qc*
     ├─► 3  Confiance / FFP      → data/processed/*trust* + *fit_for_purpose*
     └─► 4  Résultats mémoire    → reports/tables/ + reports/figures/
```

Pour un dataset **nouveau** : ouvrir `Notebook_0_...` et exécuter cellule après cellule  
(ou `Run All`). Les étapes déjà faites sont sautées sauf si `FORCE_*=True`.

---

## Données

| Dossier | Contenu |
|---|---|
| `data/raw/` | Mesures brutes (format long) |
| `data/metadata/` | Stations, logs téléchargement |
| `data/readable/` | Aperçu large (exploration) |
| `data/processed/` | QC, scores, paramètres JSON |
| `reports/tables/` | Tableaux mémoire |
| `reports/figures/` | Figures mémoire |
| `reports/figures_exploration/` | Figures exploration |

---

## Ne pas confondre

| Notion | Niveau | Notebook |
|---|---|---|
| `valide` / `a_verifier` / `suspecte` | observation | 2 |
| `trust_score` + classes FFP | série / station | 3 |
| Tableaux & figures mémoire | présentation | 4 |

Confiance relative ≠ certification métrologique.

---

## Checklist avant rédaction

1. [ ] `data/raw/opensensemap_raw_long_active_50.csv`
2. [ ] `data/processed/opensensemap_qc_metrics_station_variable.csv`
3. [ ] `data/processed/opensensemap_trust_scores_series.csv`
4. [ ] `reports/figures/` (dont `fig2b_qc_status_*.png` et figures FFP)
5. [ ] `reports/manifest_memoires_exports.csv`
