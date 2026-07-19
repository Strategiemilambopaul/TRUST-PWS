"""Parse d'un upload station + validation schéma + évaluation QC/confiance."""

from __future__ import annotations

import io
import uuid
from typing import Any

import pandas as pd
from fastapi.responses import StreamingResponse

from app.schemas import (
    AnomalyOut,
    DashboardSummary,
    EvaluateResponse,
    ImportPreview,
    SeriesTrustOut,
)
from app.services.import_service import preview_table
from app.services.session_store import get_session, save_session, update_session
from app.services.trust_engine import VARS, canon_var, run_qc_and_trust


def _read_raw(content: bytes, filename: str) -> pd.DataFrame:
    name = filename.lower()
    if name.endswith(".json"):
        df = pd.read_json(io.BytesIO(content))
    else:
        df = pd.read_csv(io.BytesIO(content))
    if df.empty:
        raise ValueError("Fichier vide.")
    return df


def _find_col(cols: list[str], *candidates: str) -> str | None:
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand in lower:
            return lower[cand]
    for c in cols:
        cl = c.lower()
        for cand in candidates:
            if cand == cl or cand in cl:
                return c
    return None


def _detect_wide_cols(cols: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for c in cols:
        cl = c.lower().strip()
        if cl in VARS:
            mapping[cl] = c
            continue
        canon = canon_var(cl)
        if canon in VARS and canon not in mapping:
            if any(k in cl for k in ("temp", "humid", "press", "druck", "feuchte")):
                mapping[canon] = c
    return mapping


def normalize_upload(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Normalise long ou large vers station_id, station_name, timestamp, variable, value, unit."""
    warnings: list[str] = []
    cols = [str(c) for c in df.columns]
    work = df.copy()
    work.columns = cols

    ts_col = _find_col(cols, "timestamp", "createdat", "datetime", "time", "date")
    if not ts_col:
        raise ValueError(
            "Colonne temporelle manquante. Attendu: timestamp, createdAt, time ou datetime."
        )

    station_col = _find_col(cols, "station_id", "boxid", "sensebox")
    name_col = _find_col(cols, "station_name", "boxname")
    unit_col = _find_col(cols, "sensor_unit", "unit", "unité", "unite")
    value_col = _find_col(cols, "value", "measurement", "valeur")
    var_col = _find_col(cols, "phenomenon", "variable")
    wide_map = _detect_wide_cols(cols)

    if var_col and var_col in wide_map.values():
        wide_map = {k: v for k, v in wide_map.items() if v != var_col}

    base_station = (
        work[station_col].astype(str)
        if station_col
        else pd.Series(["station_uploadee"] * len(work), index=work.index)
    )
    base_name = (
        work[name_col].astype(str)
        if name_col
        else pd.Series(["Station uploadée"] * len(work), index=work.index)
    )
    if not station_col:
        warnings.append("station_id absent: identifiant « station_uploadee » attribué.")

    if value_col and var_col:
        out = pd.DataFrame(
            {
                "station_id": base_station.values,
                "station_name": base_name.values,
                "timestamp": work[ts_col].values,
                "value": work[value_col].values,
                "variable": pd.Series(work[var_col]).map(canon_var).values,
                "unit": work[unit_col].astype(str).values if unit_col else "",
            }
        )
        if not unit_col:
            warnings.append(
                "Colonne unit absente: unités standard (°C, %, hPa) supposées."
            )
    elif wide_map:
        pieces = []
        for var, col in wide_map.items():
            pieces.append(
                pd.DataFrame(
                    {
                        "station_id": base_station.values,
                        "station_name": base_name.values,
                        "timestamp": work[ts_col].values,
                        "value": work[col].values,
                        "variable": var,
                        "unit": "",
                    }
                )
            )
        out = pd.concat(pieces, ignore_index=True)
        warnings.append(
            f"Format large détecté ({', '.join(sorted(wide_map))}): converti en format long."
        )
    else:
        raise ValueError(
            "Schéma invalide. Formats acceptés: "
            "(1) long: timestamp, value, phenomenon|variable [, unit] ; "
            "(2) large: timestamp + temperature/humidity/pressure."
        )

    out = out[out["variable"].isin(VARS)].copy()
    if out.empty:
        raise ValueError(
            "Aucune variable T/H/P reconnue (temperature, humidity, pressure)."
        )
    return out, warnings


def _to_response(
    eval_id: str,
    filename: str | None,
    result: dict[str, Any],
    warnings: list[str],
    message: str,
    *,
    drop_suspects: bool = False,
    drop_review: bool = False,
    n_removed: int = 0,
) -> EvaluateResponse:
    series = [SeriesTrustOut(**s) for s in result["series"]]
    anomalies = [AnomalyOut(**a) for a in result["anomalies"]]
    summary = DashboardSummary(**result["summary"])
    return EvaluateResponse(
        evaluation_id=eval_id,
        source="upload",
        filename=filename,
        summary=summary,
        series=series,
        anomalies=anomalies,
        format_ok=True,
        warnings=warnings,
        message=message,
        n_suspecte=summary.n_suspecte,
        n_a_verifier=summary.n_a_verifier,
        drop_suspects_applied=drop_suspects,
        drop_review_applied=drop_review,
        n_removed=n_removed,
        can_export=True,
    )


def evaluate_upload(content: bytes, filename: str) -> EvaluateResponse:
    preview: ImportPreview = preview_table(content, filename)
    if not preview.format_ok:
        raise ValueError(
            preview.error_message
            or "Le format du fichier n’est pas respecté."
        )

    raw = _read_raw(content, filename)
    normalized, norm_warnings = normalize_upload(raw)
    all_warnings = list(dict.fromkeys([*preview.warnings, *norm_warnings]))

    result = run_qc_and_trust(normalized)
    eval_id = f"upload-{uuid.uuid4().hex[:10]}"

    msg = (
        f"Évaluation réalisée sur « {filename} » "
        f"({result['summary']['n_observations']} obs., "
        f"{result['summary']['n_series']} série(s), "
        f"score médian {result['summary']['trust_score_median']:.3f}). "
        "Méthode alignée sur le cadre QC + confiance du mémoire."
    )
    if result["meta"]["rejected_rows"]:
        msg += f" Rejets: {result['meta']['rejected_rows']}."
    if result["meta"]["duplicates_removed"]:
        msg += f" Doublons retirés: {result['meta']['duplicates_removed']}."

    save_session(
        eval_id,
        {
            "filename": filename,
            "export_rows": result["export_rows"],
            "warnings": all_warnings,
            "drop_suspects": False,
            "drop_review": False,
        },
    )

    return _to_response(eval_id, filename, result, all_warnings, msg)


def apply_cleaning(
    evaluation_id: str,
    *,
    drop_suspects: bool = True,
    drop_review: bool = False,
) -> EvaluateResponse:
    session = get_session(evaluation_id)
    if not session:
        raise FileNotFoundError(
            "Session d’évaluation introuvable ou expirée. Relancez l’évaluation."
        )

    rows = pd.DataFrame(session["export_rows"])
    if rows.empty:
        raise ValueError("Aucune observation à nettoyer.")

    n_before = len(rows)
    mask = pd.Series(True, index=rows.index)
    if drop_suspects:
        mask &= rows["qc_status"] != "suspecte"
    if drop_review:
        mask &= rows["qc_status"] != "a_verifier"
    cleaned = rows[mask].copy()
    n_removed = n_before - len(cleaned)

    if cleaned.empty:
        raise ValueError(
            "Après suppression des observations signalées, plus aucune donnée exploitable."
        )

    # Recalcul QC/confiance sur le jeu nettoyé (valeurs d’entrée)
    for_qc = cleaned.rename(columns={"value": "value"}).copy()
    for_qc = for_qc[["station_id", "station_name", "timestamp", "variable", "value", "unit"]]
    result = run_qc_and_trust(for_qc)

    update_session(
        evaluation_id,
        export_rows=result["export_rows"],
        drop_suspects=drop_suspects,
        drop_review=drop_review,
        n_removed=n_removed,
    )

    msg = (
        f"Dataset prêt à l’emploi"
        f"{' sans valeurs suspectes' if drop_suspects else ''}"
        f"{' ni observations à vérifier' if drop_review else ''}. "
        f"{n_removed} observation(s) retirée(s) · "
        f"{result['summary']['n_observations']} conservée(s) · "
        f"score médian {result['summary']['trust_score_median']:.3f}."
    )
    return _to_response(
        evaluation_id,
        session.get("filename"),
        result,
        session.get("warnings", []),
        msg,
        drop_suspects=drop_suspects,
        drop_review=drop_review,
        n_removed=n_removed,
    )


def export_dataset_csv(
    evaluation_id: str,
    *,
    drop_suspects: bool = False,
    drop_review: bool = False,
) -> StreamingResponse:
    session = get_session(evaluation_id)
    if not session:
        raise FileNotFoundError(
            "Session d’évaluation introuvable ou expirée. Relancez l’évaluation."
        )

    rows = pd.DataFrame(session["export_rows"])
    if drop_suspects:
        rows = rows[rows["qc_status"] != "suspecte"]
    if drop_review:
        rows = rows[rows["qc_status"] != "a_verifier"]

    # Format long normalisé (conforme au cadre)
    export = pd.DataFrame(
        {
            "timestamp": rows["timestamp"],
            "station_id": rows["station_id"],
            "station_name": rows["station_name"],
            "variable": rows["variable"],
            "value": rows["value_std"].where(rows["value_std"].notna(), rows["value"]),
            "unit": rows["unit_std"].fillna(rows["unit"]),
            "qc_status": rows["qc_status"],
        }
    )

    buf = io.StringIO()
    export.to_csv(buf, index=False)
    data = io.BytesIO(buf.getvalue().encode("utf-8"))
    data.seek(0)

    base = str(session.get("filename") or "dataset").rsplit(".", 1)[0]
    suffix = "_nettoye" if (drop_suspects or drop_review) else "_normalise"
    filename = f"{base}{suffix}.csv"

    return StreamingResponse(
        data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def evaluate_corpus() -> EvaluateResponse:
    from app.services import data_service

    summary = data_service.get_dashboard_summary()
    series_raw = data_service.list_series()
    anomalies_raw = data_service.list_anomalies(limit=40)
    return EvaluateResponse(
        evaluation_id="corpus-memoire-opensensemap",
        source="corpus",
        filename=None,
        summary=summary,
        series=series_raw[:40],
        anomalies=anomalies_raw,
        format_ok=True,
        warnings=[],
        message=(
            "Évaluation du corpus de référence du mémoire "
            "(QC + confiance déjà calculés par le pipeline Python)."
        ),
        n_suspecte=summary.n_suspecte,
        n_a_verifier=summary.n_a_verifier,
        can_export=False,
    )
