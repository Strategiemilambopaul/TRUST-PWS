"""QC + confiance + FFP — exports alignés sur 00_PIPELINE_PAS_A_PAS.md"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw" / "opensensemap_raw_long_active_50.csv"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

VARS = ["temperature", "humidity", "pressure"]
LIMITS = {"temperature": (-30, 50), "humidity": (0, 100), "pressure": (850, 1100)}
UNITS = {"temperature": "°C", "humidity": "%", "pressure": "hPa"}
WEIGHTS = {
    "dim_completeness": 0.20, "dim_physical": 0.25, "dim_stability": 0.20,
    "dim_statistical": 0.15, "dim_continuity": 0.10, "dim_metadata": 0.05,
}
FFP = [
    ("usage_scientifique_restreint",
     dict(trust_min=0.85, completeness_min=0.85, physical_min=0.97,
          stability_min=0.90, statistical_min=0.90)),
    ("comparaison_relative",
     dict(trust_min=0.70, completeness_min=0.70, physical_min=0.90,
          stability_min=0.80, statistical_min=0.80)),
    ("suivi_tendances",
     dict(trust_min=0.60, completeness_min=0.60, physical_min=0.85, stability_min=0.75)),
    ("exploratoire",
     dict(trust_min=0.40, completeness_min=0.30, physical_min=0.70)),
]
MAP = {
    "trust_min": "trust_score", "completeness_min": "dim_completeness",
    "physical_min": "dim_physical", "stability_min": "dim_stability",
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


def std_units(df: pd.DataFrame) -> pd.DataFrame:
    u = df["unit"].astype(str).str.lower().str.replace(" ", "", regex=False)
    v, x = df["variable"], df["value"].astype(float)
    y, ok = x.copy(), pd.Series(False, index=df.index)

    m = v.eq("temperature")
    ok |= m & u.isin({"°c", "c", "celsius", "c°", "degc"})
    k, f = m & u.isin({"k", "kelvin"}), m & u.isin({"°f", "f", "fahrenheit"})
    y = y.mask(k, x - 273.15).mask(f, (x - 32) * 5 / 9)
    ok |= k | f

    m = v.eq("humidity")
    ok |= m & u.str.contains("%|percent|prozent|rf", regex=True, na=False)
    frac = m & u.isin({"fraction", "ratio", "0-1"})
    y, ok = y.mask(frac, x * 100), ok | frac

    m = v.eq("pressure")
    ok |= m & u.isin({"hpa", "mbar", "millibar"})
    pa, kpa = m & u.isin({"pa", "pascal"}), m & u.eq("kpa")
    y = y.mask(pa, x / 100).mask(kpa, x * 10)
    ok |= pa | kpa

    return df.assign(value_std=y, unit_std=v.map(UNITS), flag_unit_unknown=~ok)


def mean_rate(s):
    return float(s.mean()) if len(s) else np.nan


def trust_row(row):
    num = den = 0.0
    for k, w in WEIGHTS.items():
        if k in row and pd.notna(row[k]):
            num += w * float(row[k])
            den += w
    return num / den if den else np.nan


def assign_ffp(row):
    for label, rules in FFP:
        if all(float(row[MAP[k]]) >= thr for k, thr in rules.items() if pd.notna(row[MAP[k]])):
            return label
    return "non_recommande"


def main():
    print("Chargement...")
    raw = pd.read_csv(RAW, low_memory=False)
    data = raw.copy()
    data["variable"] = data["phenomenon"].map(canon_var)
    data["unit"] = data["sensor_unit"]
    data["unit_original"] = data["sensor_unit"]
    data["value_original"] = data["value"]
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
    data["value"] = pd.to_numeric(data["value"], errors="coerce")

    # Rejets traçables (export document)
    reason = pd.Series("", index=data.index)
    reason = reason.mask(data["station_id"].isna() | data["station_id"].astype(str).eq(""), "station_id_manquant")
    reason = reason.mask(reason.eq("") & data["timestamp"].isna(), "timestamp_invalide")
    reason = reason.mask(reason.eq("") & data["value"].isna(), "valeur_non_numerique")
    reason = reason.mask(reason.eq("") & ~data["variable"].isin(VARS), "variable_non_cible")
    data["rejection_reason"] = reason
    rejected = data[data["rejection_reason"].ne("")].copy()
    df = data[data["rejection_reason"].eq("")].copy()

    print(f"QC sur {len(df):,} lignes (rejets: {len(rejected):,})...")
    df = std_units(df).sort_values(["station_id", "variable", "timestamp"])

    # Doublons traçables (export document)
    df["flag_duplicate_timestamp"] = df.duplicated(
        ["station_id", "variable", "timestamp"], keep="first"
    )
    duplicates = df[df["flag_duplicate_timestamp"]].copy()
    df = df[~df["flag_duplicate_timestamp"]].copy()
    df["flag_duplicate_timestamp"] = False

    gcols = ["station_id", "variable"]
    df["delta_seconds"] = df.groupby(gcols)["timestamp"].diff().dt.total_seconds()
    freq = (
        df.loc[df["delta_seconds"] > 0].groupby(gcols)["delta_seconds"].median()
        .rename("expected_interval_seconds").reset_index()
    )
    df = df.merge(freq, on=gcols, how="left")

    df["flag_physical_implausibility"] = (
        (df["value_std"] < df["variable"].map(lambda k: LIMITS[k][0]))
        | (df["value_std"] > df["variable"].map(lambda k: LIMITS[k][1]))
    )
    df["flag_gap_before"] = (
        df["delta_seconds"] > 3 * df["expected_interval_seconds"]
    ).fillna(False)

    parts, jump_base = [], {"temperature": 8, "humidity": 30, "pressure": 5}
    for keys, g in df.groupby(gcols, sort=False):
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
                g["flag_statistical_anomaly"] = (0.6745 * (vals - med) / mad).abs() > 4.5
        parts.append(g)
    df = pd.concat(parts, ignore_index=True)
    df["flag_spatial_inconsistency"] = False  # spatial off (comme NB2 par défaut)

    major = [
        "flag_duplicate_timestamp", "flag_physical_implausibility",
        "flag_stuck_value", "flag_temporal_jump", "flag_statistical_anomaly",
        "flag_spatial_inconsistency",
    ]
    review = ["flag_unit_unknown", "flag_gap_before"]
    df["qc_status"] = np.select(
        [df[major].any(axis=1), df[review].any(axis=1)],
        ["suspecte", "a_verifier"],
        default="valide",
    )

    cov = []
    for keys, g in df.groupby(gcols):
        start, end = g["timestamp"].min(), g["timestamp"].max()
        obs = g["timestamp"].nunique()
        iv = g["expected_interval_seconds"].dropna()
        exp = obs if iv.empty or start == end else int(
            math.floor((end - start).total_seconds() / float(iv.iloc[0])) + 1
        )
        cov.append({
            "station_id": keys[0], "variable": keys[1],
            "completeness_rate": min(1.0, obs / exp) if exp else np.nan,
            "completeness_percent": 100 * min(1.0, obs / exp) if exp else np.nan,
            "observed_count": obs, "expected_count": exp,
            "start_time": start, "end_time": end,
            "expected_interval_seconds": float(iv.iloc[0]) if len(iv) else np.nan,
        })

    metrics = (
        df.groupby(gcols).agg(
            observations_qc=("value_std", "size"),
            station_name=("station_name", "first"),
            latitude=("latitude", "median"),
            longitude=("longitude", "median"),
            unit_std=("unit_std", "first"),
            unit_unknown_rate=("flag_unit_unknown", mean_rate),
            duplicate_rate=("flag_duplicate_timestamp", mean_rate),
            physical_anomaly_rate=("flag_physical_implausibility", mean_rate),
            gap_event_rate=("flag_gap_before", mean_rate),
            stuck_value_rate=("flag_stuck_value", mean_rate),
            temporal_jump_rate=("flag_temporal_jump", mean_rate),
            statistical_anomaly_rate=("flag_statistical_anomaly", mean_rate),
            spatial_inconsistency_rate=("flag_spatial_inconsistency", mean_rate),
            valid_observation_rate=("qc_status", lambda s: (s == "valide").mean()),
            suspect_observation_rate=("qc_status", lambda s: (s == "suspecte").mean()),
        ).reset_index().merge(pd.DataFrame(cov), on=gcols, how="left")
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
    t["dim_spatial"] = np.nan
    t["trust_score"] = t.apply(trust_row, axis=1)
    t["fit_for_purpose"] = t.apply(assign_ffp, axis=1)

    rank = {
        "non_recommande": 0, "exploratoire": 1, "suivi_tendances": 2,
        "comparaison_relative": 3, "usage_scientifique_restreint": 4,
    }
    inv = {v: k for k, v in rank.items()}
    stations = (
        t.groupby("station_id").agg(
            station_name=("station_name", "first"),
            n_variables=("variable", "nunique"),
            trust_score_median=("trust_score", "median"),
            trust_score_min=("trust_score", "min"),
            fit_for_purpose_station=(
                "fit_for_purpose", lambda s: inv[min(rank.get(x, 0) for x in s)]
            ),
        ).reset_index().sort_values("trust_score_median", ascending=False)
    )
    ffp_sum = (
        t["fit_for_purpose"].value_counts().rename_axis("classe")
        .reset_index(name="n_series")
    )
    ffp_sum["proportion"] = ffp_sum["n_series"] / len(t)

    print("Export (aligné document)...")
    # Étape 2
    df.to_csv(OUT / "opensensemap_measurements_qc_flagged.csv", index=False)
    df.to_parquet(OUT / "opensensemap_measurements_qc_flagged.parquet", index=False)
    metrics.to_csv(OUT / "opensensemap_qc_metrics_station_variable.csv", index=False)
    rejected.to_csv(OUT / "opensensemap_rejected_rows.csv", index=False)
    duplicates.to_csv(OUT / "opensensemap_duplicates_removed.csv", index=False)
    # Étape 3
    t.to_csv(OUT / "opensensemap_trust_scores_series.csv", index=False)
    stations.to_csv(OUT / "opensensemap_trust_scores_stations.csv", index=False)
    ffp_sum.to_csv(OUT / "opensensemap_fit_for_purpose_summary.csv", index=False)

    params = {
        "limits": LIMITS,
        "trust_weights": WEIGHTS,
        "ffp_thresholds": {a: b for a, b in FFP},
        "run_spatial_qc": False,
        "notes": "Confiance relative, non métrologique.",
    }
    for name in ("opensensemap_qc_parameters.json", "opensensemap_trust_parameters.json"):
        with open(OUT / name, "w", encoding="utf-8") as f:
            json.dump(params, f, ensure_ascii=False, indent=2)

    print(f"OK — obs={len(df):,} | rejets={len(rejected):,} | doublons={len(duplicates):,}")
    print(f"Séries={len(t)} | score méd.={t['trust_score'].median():.3f}")
    print(ffp_sum.to_string(index=False))
    print("Exports:", OUT)


if __name__ == "__main__":
    main()
