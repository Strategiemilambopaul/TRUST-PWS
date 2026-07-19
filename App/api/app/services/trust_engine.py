"""QC + score de confiance — aligné sur implement_trust_framework.py du mémoire."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

VARS = ["temperature", "humidity", "pressure"]
LIMITS = {"temperature": (-30, 50), "humidity": (0, 100), "pressure": (850, 1100)}
UNITS = {"temperature": "°C", "humidity": "%", "pressure": "hPa"}
WEIGHTS = {
    "dim_completeness": 0.20,
    "dim_physical": 0.25,
    "dim_stability": 0.20,
    "dim_statistical": 0.15,
    "dim_continuity": 0.10,
    "dim_metadata": 0.05,
}
FFP = [
    (
        "usage_scientifique_restreint",
        dict(
            trust_min=0.85,
            completeness_min=0.85,
            physical_min=0.97,
            stability_min=0.90,
            statistical_min=0.90,
        ),
    ),
    (
        "comparaison_relative",
        dict(
            trust_min=0.70,
            completeness_min=0.70,
            physical_min=0.90,
            stability_min=0.80,
            statistical_min=0.80,
        ),
    ),
    (
        "suivi_tendances",
        dict(
            trust_min=0.60,
            completeness_min=0.60,
            physical_min=0.85,
            stability_min=0.75,
        ),
    ),
    (
        "exploratoire",
        dict(
            trust_min=0.40,
            completeness_min=0.30,
            physical_min=0.70,
        ),
    ),
]
MAP = {
    "trust_min": "trust_score",
    "completeness_min": "dim_completeness",
    "physical_min": "dim_physical",
    "stability_min": "dim_stability",
    "statistical_min": "dim_statistical",
}


def canon_var(x: str) -> str:
    t = str(x).lower()
    if "temp" in t:
        return "temperature"
    if "humid" in t or "feuchte" in t:
        return "humidity"
    if "press" in t or "druck" in t:
        return "pressure"
    return t if t in VARS else "other"


def mean_rate(s: pd.Series) -> float:
    return float(s.mean()) if len(s) else float("nan")


def trust_row(row: pd.Series) -> float:
    num = den = 0.0
    for k, w in WEIGHTS.items():
        if k in row and pd.notna(row[k]):
            num += w * float(row[k])
            den += w
    return num / den if den else float("nan")


def assign_ffp(row: pd.Series) -> str:
    for label, rules in FFP:
        if all(
            float(row[MAP[k]]) >= thr
            for k, thr in rules.items()
            if pd.notna(row[MAP[k]])
        ):
            return label
    return "non_recommande"


def std_units(df: pd.DataFrame) -> pd.DataFrame:
    if "unit" not in df.columns:
        df = df.assign(unit="")
    u = df["unit"].astype(str).str.lower().str.replace(" ", "", regex=False)
    v, x = df["variable"], pd.to_numeric(df["value"], errors="coerce")
    y, ok = x.copy(), pd.Series(False, index=df.index)

    m = v.eq("temperature")
    ok |= m & u.isin({"°c", "c", "celsius", "c°", "degc", ""})
    k, f = m & u.isin({"k", "kelvin"}), m & u.isin({"°f", "f", "fahrenheit"})
    y = y.mask(k, x - 273.15).mask(f, (x - 32) * 5 / 9)
    ok |= k | f

    m = v.eq("humidity")
    ok |= m & (u.str.contains("%|percent|prozent|rf", regex=True, na=False) | u.eq(""))
    frac = m & u.isin({"fraction", "ratio", "0-1"})
    y, ok = y.mask(frac, x * 100), ok | frac

    m = v.eq("pressure")
    ok |= m & (u.isin({"hpa", "mbar", "millibar"}) | u.eq(""))
    pa, kpa = m & u.isin({"pa", "pascal"}), m & u.eq("kpa")
    y = y.mask(pa, x / 100).mask(kpa, x * 10)
    ok |= pa | kpa

    # Sans unité: on suppose déjà standard (°C, %, hPa)
    ok |= u.eq("")

    return df.assign(value_std=y, unit_std=v.map(UNITS), flag_unit_unknown=~ok)


def run_qc_and_trust(df: pd.DataFrame) -> dict[str, Any]:
    """
    df colonnes minimales: station_id, station_name, timestamp, variable, value [, unit]
    """
    data = df.copy()
    data["variable"] = data["variable"].map(canon_var)
    if "unit" not in data.columns:
        data["unit"] = ""
    if "station_name" not in data.columns:
        data["station_name"] = data["station_id"]
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
    data["value"] = pd.to_numeric(data["value"], errors="coerce")

    reason = pd.Series("", index=data.index)
    reason = reason.mask(
        data["station_id"].isna() | data["station_id"].astype(str).eq(""),
        "station_id_manquant",
    )
    reason = reason.mask(reason.eq("") & data["timestamp"].isna(), "timestamp_invalide")
    reason = reason.mask(reason.eq("") & data["value"].isna(), "valeur_non_numerique")
    reason = reason.mask(
        reason.eq("") & ~data["variable"].isin(VARS), "variable_non_cible"
    )
    rejected = int((reason.ne("")).sum())
    work = data[reason.eq("")].copy()
    if work.empty:
        raise ValueError(
            "Aucune observation exploitable (timestamp/valeur/variable T-H-P)."
        )

    work = std_units(work).sort_values(["station_id", "variable", "timestamp"])
    work["flag_duplicate_timestamp"] = work.duplicated(
        ["station_id", "variable", "timestamp"], keep="first"
    )
    duplicates = int(work["flag_duplicate_timestamp"].sum())
    work = work[~work["flag_duplicate_timestamp"]].copy()
    work["flag_duplicate_timestamp"] = False

    gcols = ["station_id", "variable"]
    work["delta_seconds"] = (
        work.groupby(gcols)["timestamp"].diff().dt.total_seconds()
    )
    freq = (
        work.loc[work["delta_seconds"] > 0]
        .groupby(gcols)["delta_seconds"]
        .median()
        .rename("expected_interval_seconds")
        .reset_index()
    )
    work = work.merge(freq, on=gcols, how="left")

    work["flag_physical_implausibility"] = (
        work["value_std"] < work["variable"].map(lambda k: LIMITS[k][0])
    ) | (work["value_std"] > work["variable"].map(lambda k: LIMITS[k][1]))
    work["flag_gap_before"] = (
        work["delta_seconds"] > 3 * work["expected_interval_seconds"]
    ).fillna(False)

    parts: list[pd.DataFrame] = []
    jump_base = {"temperature": 8, "humidity": 30, "pressure": 5}
    for keys, g in work.groupby(gcols, sort=False):
        g = g.sort_values("timestamp").copy()
        var = keys[1]
        rnd = g["value_std"].round(1)
        run = rnd.ne(rnd.shift()).cumsum()
        dur = g.groupby(run)["timestamp"].transform(
            lambda s: (s.max() - s.min()).total_seconds() / 3600
        )
        g["flag_stuck_value"] = (run.map(run.value_counts()) >= 4) & (dur >= 2)

        rate_h = g["value_std"].diff().abs() * 3600 / g["delta_seconds"]
        r = rate_h.replace([np.inf, -np.inf], np.nan).dropna()
        thr = jump_base[var]
        if len(r) >= 5:
            mad = (r - r.median()).abs().median()
            if mad and not np.isnan(mad):
                thr = max(thr, float(r.median() + 6 * 1.4826 * mad))
        g["flag_temporal_jump"] = rate_h.gt(thr).fillna(False)

        vals = g["value_std"]
        g["flag_statistical_anomaly"] = False
        if vals.notna().sum() >= 20:
            med, mad = vals.median(), (vals - vals.median()).abs().median()
            if mad and not np.isnan(mad):
                g["flag_statistical_anomaly"] = (
                    0.6745 * (vals - med) / mad
                ).abs() > 4.5
        parts.append(g)

    work = pd.concat(parts, ignore_index=True)
    work["flag_spatial_inconsistency"] = False

    major = [
        "flag_duplicate_timestamp",
        "flag_physical_implausibility",
        "flag_stuck_value",
        "flag_temporal_jump",
        "flag_statistical_anomaly",
        "flag_spatial_inconsistency",
    ]
    review = ["flag_unit_unknown", "flag_gap_before"]
    work["qc_status"] = np.select(
        [work[major].any(axis=1), work[review].any(axis=1)],
        ["suspecte", "a_verifier"],
        default="valide",
    )

    cov = []
    for keys, g in work.groupby(gcols):
        start, end = g["timestamp"].min(), g["timestamp"].max()
        obs = g["timestamp"].nunique()
        iv = g["expected_interval_seconds"].dropna()
        exp = (
            obs
            if iv.empty or start == end
            else int(math.floor((end - start).total_seconds() / float(iv.iloc[0])) + 1)
        )
        cov.append(
            {
                "station_id": keys[0],
                "variable": keys[1],
                "completeness_rate": min(1.0, obs / exp) if exp else np.nan,
            }
        )

    metrics = (
        work.groupby(gcols)
        .agg(
            observations_qc=("value_std", "size"),
            station_name=("station_name", "first"),
            unit_unknown_rate=("flag_unit_unknown", mean_rate),
            physical_anomaly_rate=("flag_physical_implausibility", mean_rate),
            gap_event_rate=("flag_gap_before", mean_rate),
            stuck_value_rate=("flag_stuck_value", mean_rate),
            temporal_jump_rate=("flag_temporal_jump", mean_rate),
            statistical_anomaly_rate=("flag_statistical_anomaly", mean_rate),
            valid_observation_rate=("qc_status", lambda s: (s == "valide").mean()),
            suspect_observation_rate=("qc_status", lambda s: (s == "suspecte").mean()),
        )
        .reset_index()
        .merge(pd.DataFrame(cov), on=gcols, how="left")
    )

    t = metrics.copy()
    t["dim_completeness"] = t["completeness_rate"].clip(0, 1)
    t["dim_physical"] = 1 - t["physical_anomaly_rate"].clip(0, 1)
    t["dim_stability"] = 1 - 0.5 * (
        t["stuck_value_rate"].clip(0, 1) + t["temporal_jump_rate"].clip(0, 1)
    )
    t["dim_statistical"] = 1 - t["statistical_anomaly_rate"].clip(0, 1)
    t["dim_continuity"] = 1 - t["gap_event_rate"].clip(0, 1)
    t["dim_metadata"] = 1 - t["unit_unknown_rate"].clip(0, 1)
    t["trust_score"] = t.apply(trust_row, axis=1)
    t["fit_for_purpose"] = t.apply(assign_ffp, axis=1)

    flag_cols = [
        "flag_physical_implausibility",
        "flag_stuck_value",
        "flag_temporal_jump",
        "flag_statistical_anomaly",
        "flag_unit_unknown",
        "flag_gap_before",
    ]
    anom = work[work["qc_status"].isin(["suspecte", "a_verifier"])].head(80)
    anomalies = []
    for _, r in anom.iterrows():
        types = [c.replace("flag_", "") for c in flag_cols if bool(r.get(c))]
        anomalies.append(
            {
                "station_id": str(r["station_id"]),
                "station_name": str(r.get("station_name", "")),
                "variable": str(r["variable"]),
                "timestamp": r["timestamp"].isoformat(),
                "value_std": float(r["value_std"]) if pd.notna(r["value_std"]) else None,
                "qc_status": str(r["qc_status"]),
                "anomaly_types": types,
            }
        )

    series = []
    for _, r in t.iterrows():
        series.append(
            {
                "station_id": str(r["station_id"]),
                "station_name": str(r.get("station_name", r["station_id"])),
                "variable": str(r["variable"]),
                "trust_score": float(r["trust_score"]),
                "fit_for_purpose": str(r["fit_for_purpose"]),
                "dim_completeness": float(r["dim_completeness"]),
                "dim_physical": float(r["dim_physical"]),
                "dim_stability": float(r["dim_stability"]),
                "dim_statistical": float(r["dim_statistical"]),
                "dim_continuity": float(r["dim_continuity"]),
                "dim_metadata": float(r["dim_metadata"]),
                "observations_qc": int(r["observations_qc"]),
                "stuck_value_rate": float(r["stuck_value_rate"]),
                "physical_anomaly_rate": float(r["physical_anomaly_rate"]),
                "temporal_jump_rate": float(r["temporal_jump_rate"]),
                "statistical_anomaly_rate": float(r["statistical_anomaly_rate"]),
                "valid_observation_rate": float(r["valid_observation_rate"]),
                "suspect_observation_rate": float(r["suspect_observation_rate"]),
            }
        )

    n_valide = int((work["qc_status"] == "valide").sum())
    n_a_verifier = int((work["qc_status"] == "a_verifier").sum())
    n_suspecte = int((work["qc_status"] == "suspecte").sum())
    n_obs = len(work)
    median = float(t["trust_score"].median()) if len(t) else 0.0
    mean = float(t["trust_score"].mean()) if len(t) else 0.0

    if median >= 0.85:
        label = "élevé"
    elif median >= 0.65:
        label = "moyen"
    else:
        label = "faible"

    export_df = work[
        [
            "station_id",
            "station_name",
            "timestamp",
            "variable",
            "value",
            "unit",
            "value_std",
            "unit_std",
            "qc_status",
        ]
    ].copy()
    export_df["timestamp"] = export_df["timestamp"].map(
        lambda x: x.isoformat() if pd.notna(x) else None
    )

    return {
        "summary": {
            "n_observations": n_obs,
            "n_stations": int(work["station_id"].nunique()),
            "n_series": len(t),
            "trust_score_mean": mean,
            "trust_score_median": median,
            "n_valide": n_valide,
            "n_a_verifier": n_a_verifier,
            "n_suspecte": n_suspecte,
            "anomalie_rate": ((n_suspecte + n_a_verifier) / n_obs) if n_obs else 0.0,
            "quality_label": label,
            "variables": sorted(t["variable"].dropna().unique().tolist()),
        },
        "series": series,
        "anomalies": anomalies,
        "export_rows": export_df.to_dict(orient="records"),
        "meta": {
            "rejected_rows": rejected,
            "duplicates_removed": duplicates,
        },
    }
