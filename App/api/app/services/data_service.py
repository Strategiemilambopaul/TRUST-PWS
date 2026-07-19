from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Optional

import numpy as np
import pandas as pd

from app import config
from app.schemas import (
    AnomalyOut,
    DashboardSummary,
    HistoryItem,
    ObservationOut,
    PipelineStepOut,
    SeriesTrustOut,
    StationOut,
)


FLAG_COLS = [
    "flag_unit_unknown",
    "flag_duplicate_timestamp",
    "flag_physical_implausibility",
    "flag_gap_before",
    "flag_stuck_value",
    "flag_temporal_jump",
    "flag_statistical_anomaly",
    "flag_spatial_inconsistency",
]


def _read_csv(path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {path}")
    return pd.read_csv(path)


@lru_cache(maxsize=1)
def load_metrics() -> pd.DataFrame:
    return _read_csv(config.METRICS_CSV)


@lru_cache(maxsize=1)
def load_trust_series() -> pd.DataFrame:
    return _read_csv(config.TRUST_SERIES_CSV)


@lru_cache(maxsize=1)
def load_trust_stations() -> pd.DataFrame:
    return _read_csv(config.TRUST_STATIONS_CSV)


@lru_cache(maxsize=1)
def load_ffp_summary() -> pd.DataFrame:
    return _read_csv(config.FFP_SUMMARY_CSV)


def _qc_path():
    if config.QC_FLAGGED_PARQUET.exists():
        return config.QC_FLAGGED_PARQUET
    if config.QC_FLAGGED_CSV.exists():
        return config.QC_FLAGGED_CSV
    return None


@lru_cache(maxsize=1)
def load_qc_status_counts() -> dict[str, int]:
    path = _qc_path()
    if path is None:
        return {"valide": 0, "a_verifier": 0, "suspecte": 0}
    if path.suffix == ".parquet":
        df = pd.read_parquet(path, columns=["qc_status"])
    else:
        df = pd.read_csv(path, usecols=["qc_status"])
    counts = df["qc_status"].value_counts().to_dict()
    return {
        "valide": int(counts.get("valide", 0)),
        "a_verifier": int(counts.get("a_verifier", 0)),
        "suspecte": int(counts.get("suspecte", 0)),
    }


def quality_label(median_trust: float) -> str:
    if median_trust >= 0.85:
        return "élevé"
    if median_trust >= 0.65:
        return "moyen"
    return "faible"


def get_dashboard_summary() -> DashboardSummary:
    trust = load_trust_series()
    stations = load_trust_stations()
    status = load_qc_status_counts()
    n_obs = sum(status.values())
    n_anom = status["suspecte"] + status["a_verifier"]
    median = float(trust["trust_score"].median())
    return DashboardSummary(
        n_observations=n_obs,
        n_stations=int(stations["station_id"].nunique()),
        n_series=len(trust),
        trust_score_mean=float(trust["trust_score"].mean()),
        trust_score_median=median,
        n_valide=status["valide"],
        n_a_verifier=status["a_verifier"],
        n_suspecte=status["suspecte"],
        anomalie_rate=(n_anom / n_obs) if n_obs else 0.0,
        quality_label=quality_label(median),
        variables=sorted(trust["variable"].dropna().unique().tolist()),
    )


def list_stations() -> list[StationOut]:
    df = load_trust_stations()
    metrics = load_metrics()
    coords = (
        metrics.groupby("station_id", as_index=False)
        .agg(latitude=("latitude", "median"), longitude=("longitude", "median"))
    )
    df = df.merge(coords, on="station_id", how="left")
    out = []
    for _, r in df.iterrows():
        out.append(
            StationOut(
                station_id=str(r["station_id"]),
                station_name=str(r.get("station_name", r["station_id"])),
                latitude=float(r["latitude"]) if pd.notna(r.get("latitude")) else None,
                longitude=float(r["longitude"]) if pd.notna(r.get("longitude")) else None,
                trust_score_median=float(r["trust_score_median"])
                if pd.notna(r.get("trust_score_median"))
                else None,
                trust_score_min=float(r["trust_score_min"])
                if pd.notna(r.get("trust_score_min"))
                else None,
                fit_for_purpose_station=str(r.get("fit_for_purpose_station"))
                if pd.notna(r.get("fit_for_purpose_station"))
                else None,
            )
        )
    return out


def list_series(
    station_id: Optional[str] = None,
    variable: Optional[str] = None,
) -> list[SeriesTrustOut]:
    df = load_trust_series().copy()
    if station_id:
        df = df[df["station_id"].astype(str) == station_id]
    if variable:
        df = df[df["variable"] == variable]

    cols = [
        "station_id", "station_name", "variable", "trust_score", "fit_for_purpose",
        "dim_completeness", "dim_physical", "dim_stability", "dim_statistical",
        "dim_continuity", "dim_metadata", "observations_qc",
        "stuck_value_rate", "physical_anomaly_rate", "temporal_jump_rate",
        "statistical_anomaly_rate", "valid_observation_rate", "suspect_observation_rate",
    ]
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan if c.startswith("dim_") or c.endswith("_rate") or c == "trust_score" else ""

    out: list[SeriesTrustOut] = []
    for _, r in df.iterrows():
        out.append(
            SeriesTrustOut(
                station_id=str(r["station_id"]),
                station_name=str(r.get("station_name", "")),
                variable=str(r["variable"]),
                trust_score=float(r["trust_score"]),
                fit_for_purpose=str(r["fit_for_purpose"]),
                dim_completeness=float(r["dim_completeness"]) if pd.notna(r["dim_completeness"]) else 0.0,
                dim_physical=float(r["dim_physical"]) if pd.notna(r["dim_physical"]) else 0.0,
                dim_stability=float(r["dim_stability"]) if pd.notna(r["dim_stability"]) else 0.0,
                dim_statistical=float(r["dim_statistical"]) if pd.notna(r["dim_statistical"]) else 0.0,
                dim_continuity=float(r["dim_continuity"]) if pd.notna(r["dim_continuity"]) else 0.0,
                dim_metadata=float(r["dim_metadata"]) if pd.notna(r["dim_metadata"]) else 0.0,
                observations_qc=int(r["observations_qc"]) if pd.notna(r["observations_qc"]) else 0,
                stuck_value_rate=float(r["stuck_value_rate"]) if pd.notna(r["stuck_value_rate"]) else 0.0,
                physical_anomaly_rate=float(r["physical_anomaly_rate"]) if pd.notna(r["physical_anomaly_rate"]) else 0.0,
                temporal_jump_rate=float(r["temporal_jump_rate"]) if pd.notna(r["temporal_jump_rate"]) else 0.0,
                statistical_anomaly_rate=float(r["statistical_anomaly_rate"]) if pd.notna(r["statistical_anomaly_rate"]) else 0.0,
                valid_observation_rate=float(r["valid_observation_rate"]) if pd.notna(r["valid_observation_rate"]) else 0.0,
                suspect_observation_rate=float(r["suspect_observation_rate"]) if pd.notna(r["suspect_observation_rate"]) else 0.0,
            )
        )
    return out


def _load_obs_slice(
    station_id: Optional[str],
    variable: Optional[str],
    limit: int,
    anomalies_only: bool = False,
) -> pd.DataFrame:
    path = _qc_path()
    if path is None:
        return pd.DataFrame()

    cols = [
        "station_id", "station_name", "variable", "timestamp",
        "value_std", "unit_std", "qc_status", *FLAG_COLS,
    ]

    if path.suffix == ".parquet":
        filters = []
        if station_id:
            filters.append(("station_id", "==", station_id))
        if variable:
            filters.append(("variable", "==", variable))
        if anomalies_only:
            # pyarrow OR filter via two reads merge, simplify: filter after
            pass
        try:
            df = pd.read_parquet(
                path,
                columns=[c for c in cols],
                filters=filters or None,
            )
        except Exception:
            df = pd.read_parquet(path, columns=[c for c in cols])
            if station_id:
                df = df[df["station_id"].astype(str) == station_id]
            if variable:
                df = df[df["variable"] == variable]
        if anomalies_only:
            df = df[df["qc_status"].isin(["suspecte", "a_verifier"])]
        if not station_id and not anomalies_only and len(df) > limit * 5:
            df = df.sample(n=min(limit * 5, len(df)), random_state=42)
        return df.head(limit)

    # CSV: stream filter
    chunks = []
    usecols = [c for c in cols]
    for chunk in pd.read_csv(path, usecols=usecols, chunksize=200_000):
        if station_id:
            chunk = chunk[chunk["station_id"].astype(str) == station_id]
        if variable:
            chunk = chunk[chunk["variable"] == variable]
        if anomalies_only:
            chunk = chunk[chunk["qc_status"].isin(["suspecte", "a_verifier"])]
        if not chunk.empty:
            chunks.append(chunk)
        if sum(len(c) for c in chunks) >= limit:
            break
    if not chunks:
        return pd.DataFrame(columns=usecols)
    return pd.concat(chunks, ignore_index=True).head(limit)


def list_observations(
    station_id: Optional[str] = None,
    variable: Optional[str] = None,
    limit: int = 500,
) -> list[ObservationOut]:
    df = _load_obs_slice(station_id, variable, limit, anomalies_only=False)
    return _rows_to_obs(df)


def list_anomalies(
    station_id: Optional[str] = None,
    variable: Optional[str] = None,
    limit: int = 300,
) -> list[AnomalyOut]:
    df = _load_obs_slice(station_id, variable, limit, anomalies_only=True)
    out: list[AnomalyOut] = []
    for _, r in df.iterrows():
        types = [c.replace("flag_", "") for c in FLAG_COLS if bool(r.get(c, False))]
        out.append(
            AnomalyOut(
                station_id=str(r["station_id"]),
                station_name=str(r["station_name"]) if pd.notna(r.get("station_name")) else None,
                variable=str(r["variable"]),
                timestamp=str(r["timestamp"]),
                value_std=float(r["value_std"]) if pd.notna(r.get("value_std")) else None,
                qc_status=str(r["qc_status"]),
                anomaly_types=types or [str(r["qc_status"])],
            )
        )
    return out


def _rows_to_obs(df: pd.DataFrame) -> list[ObservationOut]:
    out: list[ObservationOut] = []
    for _, r in df.iterrows():
        flags = {c.replace("flag_", ""): bool(r.get(c, False)) for c in FLAG_COLS if c in df.columns}
        out.append(
            ObservationOut(
                station_id=str(r["station_id"]),
                station_name=str(r["station_name"]) if pd.notna(r.get("station_name")) else None,
                variable=str(r["variable"]),
                timestamp=str(r["timestamp"]),
                value_std=float(r["value_std"]) if pd.notna(r.get("value_std")) else None,
                unit_std=str(r["unit_std"]) if pd.notna(r.get("unit_std")) else None,
                qc_status=str(r["qc_status"]),
                flags=flags,
            )
        )
    return out


def pipeline_steps() -> list[PipelineStepOut]:
    summary = get_dashboard_summary()
    trust = load_trust_series()
    return [
        PipelineStepOut(
            step=1, key="acquisition", title="Acquisition",
            description="Corpus openSenseMap T/H/P, stations outdoor actives.",
            status="done",
            metrics={"stations": summary.n_stations, "observations": summary.n_observations},
        ),
        PipelineStepOut(
            step=2, key="validation", title="Validation schéma",
            description="Contrôle des colonnes, types et variables cibles.",
            status="done",
            metrics={"variables": summary.variables},
        ),
        PipelineStepOut(
            step=3, key="nettoyage", title="Nettoyage / unités",
            description="Standardisation °C, %, hPa et retrait des doublons temporels.",
            status="done",
            metrics={"series": summary.n_series},
        ),
        PipelineStepOut(
            step=4, key="coherence", title="Contrôle de cohérence",
            description="Plages physiques, gaps, continuité temporelle.",
            status="done",
            metrics={"a_verifier": summary.n_a_verifier},
        ),
        PipelineStepOut(
            step=5, key="anomalies", title="Détection d'anomalies",
            description="Valeurs figées, sauts, anomalies statistiques MAD.",
            status="done",
            metrics={"suspecte": summary.n_suspecte, "taux": round(summary.anomalie_rate, 4)},
        ),
        PipelineStepOut(
            step=6, key="indicateurs", title="Indicateurs QC",
            description="Taux agrégés par station et variable.",
            status="done",
            metrics={"n_metrics_rows": len(load_metrics())},
        ),
        PipelineStepOut(
            step=7, key="score", title="Score de confiance",
            description="Dimensions pondérées renormalisées (spatial off).",
            status="done",
            metrics={
                "median": round(summary.trust_score_median, 4),
                "mean": round(summary.trust_score_mean, 4),
            },
        ),
        PipelineStepOut(
            step=8, key="decision", title="Décision fit-for-purpose",
            description="Classe d'usage par série, agrégation station par minimum.",
            status="done",
            metrics={
                "classes": trust["fit_for_purpose"].value_counts().to_dict(),
            },
        ),
    ]


def evaluation_history(limit: int = 50) -> list[HistoryItem]:
    stations = load_trust_stations().sort_values("trust_score_median", ascending=False)
    items: list[HistoryItem] = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for i, (_, r) in enumerate(stations.head(limit).iterrows()):
        sid = str(r["station_id"])
        score = float(r["trust_score_median"])
        ffp = str(r["fit_for_purpose_station"])
        # approx anomalies from series
        series = load_trust_series()
        sub = series[series["station_id"].astype(str) == sid]
        n_anom = int((sub["suspect_observation_rate"] * sub["observations_qc"]).sum())
        eid = hashlib.md5(f"{sid}-{score}".encode()).hexdigest()[:10]
        items.append(
            HistoryItem(
                id=eid,
                date=today,
                station_name=str(r["station_name"]),
                station_id=sid,
                trust_score=score,
                status="élevé" if score >= 0.85 else ("moyen" if score >= 0.65 else "faible"),
                fit_for_purpose=ffp,
                n_anomalies=n_anom,
                summary=f"Classe station: {ffp}. Score médian {score:.3f}.",
            )
        )
    return items


def timeseries_sample(
    station_id: str,
    variable: str,
    limit: int = 800,
) -> list[dict[str, Any]]:
    df = _load_obs_slice(station_id, variable, limit * 3, anomalies_only=False)
    if df.empty:
        return []
    df = df.sort_values("timestamp").tail(limit)
    return [
        {
            "timestamp": str(r["timestamp"]),
            "value": float(r["value_std"]) if pd.notna(r["value_std"]) else None,
            "qc_status": str(r["qc_status"]),
        }
        for _, r in df.iterrows()
    ]


def ffp_summary() -> list[dict[str, Any]]:
    df = load_ffp_summary()
    return df.to_dict(orient="records")
