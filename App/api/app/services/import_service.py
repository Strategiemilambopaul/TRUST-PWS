from __future__ import annotations

import io
from typing import Any

import pandas as pd

from app.schemas import ImportPreview

REQUIRED_LONG = [
    {"timestamp", "value", "phenomenon"},
    {"timestamp", "value", "variable"},
    {"createdat", "value", "phenomenon"},
    {"createdat", "value", "variable"},
    {"time", "value", "phenomenon"},
    {"time", "value", "variable"},
    {"datetime", "value", "phenomenon"},
    {"datetime", "value", "variable"},
]

WIDE_VARS = ("temperature", "humidity", "pressure")


def _has_time_col(cols_lower: list[str]) -> bool:
    return any(
        any(k in c for k in ("timestamp", "createdat", "datetime", "time", "date"))
        for c in cols_lower
    )


def _is_wide_ok(cols_lower: list[str]) -> bool:
    if not _has_time_col(cols_lower):
        return False
    return any(
        c in WIDE_VARS or any(v in c for v in ("temp", "humid", "press"))
        for c in cols_lower
    )


def _is_long_ok(cols_lower: list[str]) -> bool:
    for req in REQUIRED_LONG:
        if all(any(r in c for c in cols_lower) for r in req):
            return True
    return False


def preview_table(content: bytes, filename: str) -> ImportPreview:
    name = filename.lower()
    warnings: list[str] = []

    if name.endswith(".json"):
        df = pd.read_json(io.BytesIO(content))
    else:
        df = pd.read_csv(io.BytesIO(content))

    if df.empty:
        raise ValueError("Fichier vide.")

    cols = [str(c) for c in df.columns]
    cols_lower = [c.lower() for c in cols]
    lower = {c.lower(): c for c in cols}

    detected = []
    for key in ("temperature", "humidity", "pressure", "phenomenon", "variable"):
        if key in lower or any(key in c.lower() for c in cols):
            detected.append(key)

    long_ok = _is_long_ok(cols_lower)
    wide_ok = _is_wide_ok(cols_lower)
    format_ok = long_ok or wide_ok
    error_message = None

    if not format_ok:
        error_message = (
            "Le format du fichier n’est pas respecté.\n\n"
            "Formats acceptés :\n"
            "• long : timestamp, value, phenomenon|variable [, unit]\n"
            "• large : timestamp + temperature / humidity / pressure\n\n"
            f"Colonnes détectées : {', '.join(cols)}"
        )
        warnings.append(error_message)
    elif wide_ok and not long_ok:
        warnings.append(
            "Format large détecté (timestamp + T/H/P). Il sera converti en format long."
        )

    for extra in ("wind", "rain", "precipitation", "radiation", "luminosity"):
        if any(extra in c.lower() for c in cols):
            warnings.append(
                f"Colonne liée à « {extra} » détectée: hors périmètre du mémoire (T/H/P)."
            )

    sample = df.head(20).where(pd.notna(df.head(20)), None).to_dict(orient="records")
    clean_sample: list[dict[str, Any]] = []
    for row in sample:
        clean_sample.append({str(k): (None if pd.isna(v) else v) for k, v in row.items()})

    return ImportPreview(
        columns=cols,
        n_rows=len(df),
        sample=clean_sample,
        detected_variables=sorted(set(detected)),
        warnings=warnings,
        format_ok=format_ok,
        error_message=error_message,
    )
