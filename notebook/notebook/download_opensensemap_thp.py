"""Télécharge T/H/P openSenseMap → data/raw/opensensemap_raw_long_active_50.csv"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

BASE = "https://api.opensensemap.org"
FROM, TO, CHUNK_DAYS = "2026-06-15T00:00:00Z", "2026-07-15T00:00:00Z", 7
ROOT = Path(__file__).resolve().parent
RAW, META = ROOT / "data" / "raw", ROOT / "data" / "metadata"
RAW.mkdir(parents=True, exist_ok=True)
META.mkdir(parents=True, exist_ok=True)

STATIONS = META / "stations_selectionnees_actives.csv"
OUT = RAW / "opensensemap_raw_long_active_50.csv"
CKPT = RAW / "download_checkpoint.parquet"
LOG = META / "download_log_active_50.csv"
ERR = META / "error_log_active_50.csv"

SENSORS = {
    "temperature": "temperature_sensor_id",
    "humidity": "humidity_sensor_id",
    "pressure": "pressure_sensor_id",
}


def chunks(start: str, end: str, days: int):
    a = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    b = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    out = []
    while a < b:
        nxt = min(a + timedelta(days=days), b)
        out.append((a.strftime("%Y-%m-%dT%H:%M:%SZ"), nxt.strftime("%Y-%m-%dT%H:%M:%SZ")))
        a = nxt
    return out


def fetch(box_id, sensor_id, t0, t1, retries=5):
    url = f"{BASE}/boxes/{box_id}/data/{sensor_id}"
    for i in range(retries):
        try:
            r = requests.get(url, params={"from-date": t0, "to-date": t1}, timeout=120)
            if r.status_code == 200:
                data = r.json()
                return pd.DataFrame(data if isinstance(data, list) else ([data] if data else []))
            if r.status_code not in {429, 500, 502, 503, 504}:
                return pd.DataFrame()
        except requests.RequestException:
            time.sleep(min(30, 2 ** i))
            continue
        time.sleep(min(30, 2 ** i))
    return pd.DataFrame()


def main():
    stations = pd.read_csv(STATIONS)
    periods = chunks(FROM, TO, CHUNK_DAYS)
    frames, done = [], set()

    if CKPT.exists():
        ck = pd.read_parquet(CKPT)
        frames.append(ck)
        done = set(
            zip(ck["station_id"], ck["phenomenon"], ck["chunk_start"], ck["chunk_end"])
        )
        print(f"Reprise: {len(ck):,} lignes, {len(done)} tâches faites")

    tasks = [
        (s, var, col, t0, t1)
        for _, s in stations.iterrows()
        for var, col in SENSORS.items()
        for t0, t1 in periods
        if (s["box_id"], var, t0, t1) not in done
    ]
    print(f"Tâches restantes: {len(tasks)}")
    logs, errors = [], []

    for i, (s, var, col, t0, t1) in enumerate(tasks, 1):
        print(f"[{i}/{len(tasks)}] {s['station_name']} | {var} | {t0[:10]}", flush=True)
        df = fetch(s["box_id"], s[col], t0, t1)
        row = {
            "station_id": s["box_id"], "station_name": s["station_name"],
            "phenomenon": var, "sensor_id": s[col],
            "chunk_start": t0, "chunk_end": t1, "n_rows": len(df),
        }
        logs.append(row)
        if df.empty:
            errors.append({**row, "error": "empty_or_failed"})
            print("  vide/erreur", flush=True)
            time.sleep(0.5)
            continue
        df = df.assign(
            station_id=s["box_id"],
            station_name=s["station_name"],
            latitude=s["latitude"],
            longitude=s["longitude"],
            exposure=s["exposure"],
            phenomenon=var,
            sensor_id=s[col],
            sensor_title=s.get(f"{var}_title"),
            sensor_unit=s.get(f"{var}_unit"),
            sensor_type=s.get(f"{var}_sensor_type"),
            chunk_start=t0,
            chunk_end=t1,
        )
        frames.append(df)
        print(f"  +{len(df)}", flush=True)
        if i % 10 == 0 or i == len(tasks):
            pd.concat(frames, ignore_index=True).to_parquet(CKPT, index=False)
        time.sleep(0.4)

    if not frames:
        raise RuntimeError("Aucune donnée récupérée.")

    raw = pd.concat(frames, ignore_index=True)
    tcol = next(c for c in ["createdAt", "timestamp", "time"] if c in raw.columns)
    raw["timestamp"] = pd.to_datetime(raw[tcol], utc=True, errors="coerce")
    raw["value"] = pd.to_numeric(raw["value"], errors="coerce")
    keep = [
        "station_id", "station_name", "latitude", "longitude", "exposure",
        "phenomenon", "sensor_id", "sensor_title", "sensor_unit", "sensor_type",
        "timestamp", "value", "chunk_start", "chunk_end",
    ]
    out = (
        raw[keep]
        .drop_duplicates(["station_id", "phenomenon", "timestamp", "value"])
        .sort_values(["station_id", "phenomenon", "timestamp"])
        .reset_index(drop=True)
    )
    out.to_csv(OUT, index=False, encoding="utf-8")
    pd.DataFrame(logs).to_csv(LOG, index=False, encoding="utf-8")
    pd.DataFrame(errors).to_csv(ERR, index=False, encoding="utf-8")
    print(f"OK → {OUT} ({len(out):,} lignes, {out['station_id'].nunique()} stations)")
    print(f"Logs → {LOG.name} | erreurs → {ERR.name} ({len(errors)})")


if __name__ == "__main__":
    main()
