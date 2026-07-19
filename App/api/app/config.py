from pathlib import Path

# Racine SI : App/api/app -> parents[3] = SI
SI_ROOT = Path(__file__).resolve().parents[3]
DATA_PROCESSED = SI_ROOT / "notebook" / "notebook" / "data" / "processed"
DATA_RAW = SI_ROOT / "notebook" / "notebook" / "data" / "raw"
DATA_META = SI_ROOT / "notebook" / "notebook" / "data" / "metadata"

METRICS_CSV = DATA_PROCESSED / "opensensemap_qc_metrics_station_variable.csv"
TRUST_SERIES_CSV = DATA_PROCESSED / "opensensemap_trust_scores_series.csv"
TRUST_STATIONS_CSV = DATA_PROCESSED / "opensensemap_trust_scores_stations.csv"
FFP_SUMMARY_CSV = DATA_PROCESSED / "opensensemap_fit_for_purpose_summary.csv"
QC_FLAGGED_PARQUET = DATA_PROCESSED / "opensensemap_measurements_qc_flagged.parquet"
QC_FLAGGED_CSV = DATA_PROCESSED / "opensensemap_measurements_qc_flagged.csv"
STATIONS_CSV = DATA_META / "stations_selectionnees_actives.csv"

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://localhost:5174",
]
