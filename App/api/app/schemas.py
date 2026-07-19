from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    n_observations: int
    n_stations: int
    n_series: int
    trust_score_mean: float
    trust_score_median: float
    n_valide: int
    n_a_verifier: int
    n_suspecte: int
    anomalie_rate: float
    quality_label: Literal["élevé", "moyen", "faible"]
    variables: list[str]


class StationOut(BaseModel):
    station_id: str
    station_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    trust_score_median: Optional[float] = None
    trust_score_min: Optional[float] = None
    fit_for_purpose_station: Optional[str] = None


class SeriesTrustOut(BaseModel):
    station_id: str
    station_name: str
    variable: str
    trust_score: float
    fit_for_purpose: str
    dim_completeness: float
    dim_physical: float
    dim_stability: float
    dim_statistical: float
    dim_continuity: float
    dim_metadata: float
    observations_qc: int
    stuck_value_rate: float
    physical_anomaly_rate: float
    temporal_jump_rate: float
    statistical_anomaly_rate: float
    valid_observation_rate: float
    suspect_observation_rate: float


class ObservationOut(BaseModel):
    station_id: str
    station_name: Optional[str] = None
    variable: str
    timestamp: str
    value_std: Optional[float] = None
    unit_std: Optional[str] = None
    qc_status: str
    flags: dict[str, bool] = Field(default_factory=dict)


class AnomalyOut(BaseModel):
    station_id: str
    station_name: Optional[str] = None
    variable: str
    timestamp: str
    value_std: Optional[float] = None
    qc_status: str
    anomaly_types: list[str]


class PipelineStepOut(BaseModel):
    step: int
    key: str
    title: str
    description: str
    status: Literal["done", "active", "pending"]
    metrics: dict[str, Any] = Field(default_factory=dict)


class HistoryItem(BaseModel):
    id: str
    date: str
    station_name: str
    station_id: str
    trust_score: float
    status: str
    fit_for_purpose: str
    n_anomalies: int
    summary: str


class ImportPreview(BaseModel):
    columns: list[str]
    n_rows: int
    sample: list[dict[str, Any]]
    detected_variables: list[str]
    warnings: list[str]
    format_ok: bool = True
    error_message: Optional[str] = None


class IoTReadingIn(BaseModel):
    device_id: str = "arduino-pws"
    station_name: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    timestamp: Optional[str] = None


class IoTBatchIn(BaseModel):
    readings: list[IoTReadingIn] = Field(default_factory=list)


class EvaluateResponse(BaseModel):
    evaluation_id: str
    source: Literal["upload", "corpus", "iot"] = "corpus"
    filename: Optional[str] = None
    summary: DashboardSummary
    series: list[SeriesTrustOut] = Field(default_factory=list)
    anomalies: list[AnomalyOut] = Field(default_factory=list)
    format_ok: bool = True
    warnings: list[str] = Field(default_factory=list)
    message: str
    n_suspecte: int = 0
    n_a_verifier: int = 0
    drop_suspects_applied: bool = False
    drop_review_applied: bool = False
    n_removed: int = 0
    can_export: bool = False


class CleanRequest(BaseModel):
    drop_suspects: bool = True
    drop_review: bool = False
