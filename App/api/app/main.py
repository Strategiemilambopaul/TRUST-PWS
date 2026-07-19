from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.schemas import CleanRequest, EvaluateResponse, IoTBatchIn, IoTReadingIn
from app.services import data_service, iot_service
from app.services.evaluate_service import (
    apply_cleaning,
    evaluate_corpus,
    evaluate_upload,
    export_dataset_csv,
)
from app.services.import_service import preview_table

app = FastAPI(
    title="Trust PWS API",
    description=(
        "API du prototype scientifique: cadre reproductible d'évaluation "
        "de la confiance pour données PWS low-cost (T/H/P)."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "data_processed": str(config.DATA_PROCESSED),
        "metrics_exists": config.METRICS_CSV.exists(),
        "trust_exists": config.TRUST_SERIES_CSV.exists(),
    }


@app.get("/dashboard/summary")
def dashboard_summary():
    try:
        return data_service.get_dashboard_summary()
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


@app.get("/stations")
def stations():
    try:
        return data_service.list_stations()
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


@app.get("/series")
def series(
    station_id: Optional[str] = None,
    variable: Optional[str] = None,
):
    try:
        return data_service.list_series(station_id, variable)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


@app.get("/observations")
def observations(
    station_id: Optional[str] = Query(None),
    variable: Optional[str] = Query(None),
    limit: int = Query(400, ge=1, le=5000),
):
    try:
        if not station_id:
            sts = data_service.list_stations()
            if not sts:
                return []
            station_id = sts[0].station_id
        return data_service.list_observations(station_id, variable, limit)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


@app.get("/timeseries")
def timeseries(
    station_id: str,
    variable: str = "temperature",
    limit: int = Query(800, ge=50, le=5000),
):
    try:
        return data_service.timeseries_sample(station_id, variable, limit)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


@app.get("/anomalies")
def anomalies(
    station_id: Optional[str] = None,
    variable: Optional[str] = None,
    limit: int = Query(300, ge=1, le=2000),
):
    try:
        return data_service.list_anomalies(station_id, variable, limit)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


@app.get("/pipeline/steps")
def pipeline_steps():
    try:
        return data_service.pipeline_steps()
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


@app.get("/trust/ffp-summary")
def ffp_summary():
    try:
        return data_service.ffp_summary()
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


@app.get("/history")
def history(limit: int = Query(40, ge=1, le=200)):
    try:
        return data_service.evaluation_history(limit)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


@app.post("/import/preview")
async def import_preview(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(400, "Fichier vide.")
    try:
        return preview_table(content, file.filename or "data.csv")
    except Exception as e:
        raise HTTPException(400, f"Impossible de lire le fichier: {e}") from e


@app.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(file: UploadFile | None = File(None)):
    """
    Sans fichier: synthèse du corpus mémoire.
    Avec fichier: validation du schéma puis QC + score de confiance
    (même logique que implement_trust_framework.py).
    """
    if file is None:
        try:
            return evaluate_corpus()
        except FileNotFoundError as e:
            raise HTTPException(404, str(e)) from e

    content = await file.read()
    if not content:
        raise HTTPException(400, "Fichier vide.")
    try:
        return evaluate_upload(content, file.filename or "upload.csv")
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(400, f"Évaluation impossible: {e}") from e


@app.post("/evaluate/{evaluation_id}/clean", response_model=EvaluateResponse)
def evaluate_clean(evaluation_id: str, body: CleanRequest):
    """Retire les observations suspectes (et optionnellement à vérifier), puis recalcule."""
    try:
        return apply_cleaning(
            evaluation_id,
            drop_suspects=body.drop_suspects,
            drop_review=body.drop_review,
        )
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@app.get("/evaluate/{evaluation_id}/export")
def evaluate_export(
    evaluation_id: str,
    drop_suspects: bool = Query(False),
    drop_review: bool = Query(False),
):
    """Exporte le dataset au format long normalisé (CSV)."""
    try:
        return export_dataset_csv(
            evaluation_id,
            drop_suspects=drop_suspects,
            drop_review=drop_review,
        )
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


# --- IoT / Arduino -----------------------------------------------------------


@app.get("/iot/status")
def iot_status():
    return iot_service.status()


@app.get("/iot/readings")
def iot_readings(limit: int = Query(80, ge=1, le=2000)):
    return iot_service.list_readings(limit)


@app.post("/iot/ingest")
def iot_ingest(body: IoTReadingIn):
    """Point d’entrée principal pour ESP32 / Arduino (JSON T/H/P)."""
    try:
        return iot_service.ingest_reading(
            device_id=body.device_id,
            temperature=body.temperature,
            humidity=body.humidity,
            pressure=body.pressure,
            timestamp=body.timestamp,
            station_name=body.station_name,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@app.get("/iot/ingest")
def iot_ingest_get(
    t: Optional[float] = Query(None, description="temperature °C"),
    h: Optional[float] = Query(None, description="humidity %"),
    p: Optional[float] = Query(None, description="pressure hPa"),
    device_id: str = Query("arduino-pws"),
):
    """Variante GET simple pour sketches Arduino basiques."""
    try:
        return iot_service.ingest_reading(
            device_id=device_id,
            temperature=t,
            humidity=h,
            pressure=p,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@app.post("/iot/ingest/batch")
def iot_ingest_batch(body: IoTBatchIn):
    if not body.readings:
        raise HTTPException(400, "Liste readings vide.")
    try:
        return iot_service.ingest_batch([r.model_dump() for r in body.readings])
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@app.delete("/iot/buffer")
def iot_clear():
    return iot_service.clear_buffer()


@app.post("/iot/evaluate", response_model=EvaluateResponse)
def iot_evaluate():
    try:
        return iot_service.evaluate_buffer()
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@app.post("/iot/simulate")
def iot_simulate(n: int = Query(30, ge=5, le=200)):
    """Démo sans matériel : remplit le buffer avec un flux synthétique."""
    return iot_service.simulate_demo(n=n)
