"""Buffer temps réel pour capteurs IoT / Arduino (T/H/P)."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Optional

import pandas as pd

from app.services.session_store import save_session
from app.services.trust_engine import run_qc_and_trust

MAX_POINTS = 5000
_lock = Lock()
_buffer: deque[dict[str, Any]] = deque(maxlen=MAX_POINTS)
_meta: dict[str, Any] = {
    "last_device_id": None,
    "last_seen_at": None,
    "total_received": 0,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ingest_reading(
    *,
    device_id: str = "arduino-pws",
    temperature: Optional[float] = None,
    humidity: Optional[float] = None,
    pressure: Optional[float] = None,
    timestamp: Optional[str] = None,
    station_name: Optional[str] = None,
) -> dict[str, Any]:
    if temperature is None and humidity is None and pressure is None:
        raise ValueError(
            "Au moins une mesure requise: temperature, humidity ou pressure."
        )

    ts = timestamp or _now_iso()
    # Valider timestamp
    try:
        pd.to_datetime(ts, utc=True)
    except Exception as e:
        raise ValueError(f"timestamp invalide: {e}") from e

    name = station_name or f"Station IoT ({device_id})"
    rows: list[dict[str, Any]] = []
    mapping = {
        "temperature": temperature,
        "humidity": humidity,
        "pressure": pressure,
    }
    units = {"temperature": "°C", "humidity": "%", "pressure": "hPa"}

    with _lock:
        for var, val in mapping.items():
            if val is None:
                continue
            try:
                num = float(val)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Valeur {var} non numérique: {val}") from e
            row = {
                "timestamp": ts,
                "station_id": str(device_id),
                "station_name": name,
                "variable": var,
                "value": num,
                "unit": units[var],
                "received_at": _now_iso(),
            }
            _buffer.append(row)
            rows.append(row)

        _meta["last_device_id"] = str(device_id)
        _meta["last_seen_at"] = _now_iso()
        _meta["total_received"] = int(_meta["total_received"]) + len(rows)

    return {
        "accepted": len(rows),
        "device_id": device_id,
        "timestamp": ts,
        "buffer_size": len(_buffer),
        "rows": rows,
    }


def ingest_batch(readings: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = 0
    last = None
    for r in readings:
        last = ingest_reading(
            device_id=str(r.get("device_id") or r.get("station_id") or "arduino-pws"),
            temperature=r.get("temperature"),
            humidity=r.get("humidity"),
            pressure=r.get("pressure"),
            timestamp=r.get("timestamp"),
            station_name=r.get("station_name"),
        )
        accepted += last["accepted"]
    return {
        "accepted": accepted,
        "buffer_size": status()["buffer_size"],
        "last": last,
    }


def status() -> dict[str, Any]:
    with _lock:
        n = len(_buffer)
        last = _buffer[-1] if n else None
        devices = sorted({r["station_id"] for r in _buffer})
        return {
            "buffer_size": n,
            "max_points": MAX_POINTS,
            "total_received": _meta["total_received"],
            "last_device_id": _meta["last_device_id"],
            "last_seen_at": _meta["last_seen_at"],
            "devices": devices,
            "last_reading": last,
            "ready_for_evaluation": n >= 12,
            "min_recommended": 12,
        }


def list_readings(limit: int = 100) -> list[dict[str, Any]]:
    with _lock:
        items = list(_buffer)
    return items[-limit:]


def clear_buffer() -> dict[str, Any]:
    with _lock:
        _buffer.clear()
        _meta["last_device_id"] = None
        _meta["last_seen_at"] = None
        # garder total_received comme compteur de session globale
    return {"cleared": True, "buffer_size": 0}


def evaluate_buffer() -> Any:
    with _lock:
        rows = list(_buffer)
    if len(rows) < 6:
        raise ValueError(
            "Buffer IoT trop court. Envoyez au moins ~6 observations "
            "(idéalement ≥ 12 points T/H/P) avant d’évaluer."
        )

    df = pd.DataFrame(rows)
    # format long déjà prêt pour trust_engine
    for_qc = df[["station_id", "station_name", "timestamp", "variable", "value", "unit"]].copy()
    result = run_qc_and_trust(for_qc)

    eval_id = f"iot-{pd.Timestamp.utcnow().strftime('%Y%m%d%H%M%S')}"
    device = rows[-1]["station_id"]
    filename = f"iot_{device}.csv"

    save_session(
        eval_id,
        {
            "filename": filename,
            "export_rows": result["export_rows"],
            "warnings": ["Source: flux IoT / Arduino (buffer temps réel)."],
            "drop_suspects": False,
            "drop_review": False,
        },
    )

    msg = (
        f"Évaluation du flux IoT « {device} » "
        f"({result['summary']['n_observations']} obs., "
        f"score médian {result['summary']['trust_score_median']:.3f})."
    )
    from app.schemas import (
        AnomalyOut,
        DashboardSummary,
        EvaluateResponse,
        SeriesTrustOut,
    )

    return EvaluateResponse(
        evaluation_id=eval_id,
        source="iot",
        filename=filename,
        summary=DashboardSummary(**result["summary"]),
        series=[SeriesTrustOut(**s) for s in result["series"]],
        anomalies=[AnomalyOut(**a) for a in result["anomalies"]],
        format_ok=True,
        warnings=["Source: flux IoT / Arduino (buffer temps réel)."],
        message=msg,
        n_suspecte=result["summary"]["n_suspecte"],
        n_a_verifier=result["summary"]["n_a_verifier"],
        can_export=True,
    )


def simulate_demo(n: int = 30, device_id: str = "arduino-demo") -> dict[str, Any]:
    """Génère un petit flux réaliste pour tester sans matériel."""
    import math
    import random

    base_t, base_h, base_p = 21.0, 52.0, 1013.0
    now = datetime.now(timezone.utc)
    accepted = 0
    for i in range(n):
        ts = (now - pd.Timedelta(minutes=10 * (n - i))).isoformat()
        t = base_t + 1.2 * math.sin(i / 5) + random.uniform(-0.3, 0.3)
        h = base_h + 3 * math.sin(i / 7) + random.uniform(-1, 1)
        p = base_p + 0.4 * math.sin(i / 9) + random.uniform(-0.2, 0.2)
        # injecte 1 valeur suspecte
        if i == n // 2:
            h = 125.0
        out = ingest_reading(
            device_id=device_id,
            temperature=round(t, 2),
            humidity=round(h, 2),
            pressure=round(p, 2),
            timestamp=ts,
            station_name="Arduino démo",
        )
        accepted += out["accepted"]
    return {"accepted": accepted, "buffer_size": status()["buffer_size"], "device_id": device_id}
