export type QualityLabel = 'élevé' | 'moyen' | 'faible'

export interface DashboardSummary {
  n_observations: number
  n_stations: number
  n_series: number
  trust_score_mean: number
  trust_score_median: number
  n_valide: number
  n_a_verifier: number
  n_suspecte: number
  anomalie_rate: number
  quality_label: QualityLabel
  variables: string[]
}

export interface Station {
  station_id: string
  station_name: string
  latitude?: number | null
  longitude?: number | null
  trust_score_median?: number | null
  trust_score_min?: number | null
  fit_for_purpose_station?: string | null
}

export interface SeriesTrust {
  station_id: string
  station_name: string
  variable: string
  trust_score: number
  fit_for_purpose: string
  dim_completeness: number
  dim_physical: number
  dim_stability: number
  dim_statistical: number
  dim_continuity: number
  dim_metadata: number
  observations_qc: number
  stuck_value_rate: number
  physical_anomaly_rate: number
  temporal_jump_rate: number
  statistical_anomaly_rate: number
  valid_observation_rate: number
  suspect_observation_rate: number
}

export interface Observation {
  station_id: string
  station_name?: string | null
  variable: string
  timestamp: string
  value_std?: number | null
  unit_std?: string | null
  qc_status: string
  flags: Record<string, boolean>
}

export interface Anomaly {
  station_id: string
  station_name?: string | null
  variable: string
  timestamp: string
  value_std?: number | null
  qc_status: string
  anomaly_types: string[]
}

export interface PipelineStep {
  step: number
  key: string
  title: string
  description: string
  status: 'done' | 'active' | 'pending'
  metrics: Record<string, unknown>
}

export interface HistoryItem {
  id: string
  date: string
  station_name: string
  station_id: string
  trust_score: number
  status: string
  fit_for_purpose: string
  n_anomalies: number
  summary: string
}

export interface ImportPreview {
  columns: string[]
  n_rows: number
  sample: Record<string, unknown>[]
  detected_variables: string[]
  warnings: string[]
  format_ok: boolean
  error_message?: string | null
}

export interface EvaluateResult {
  evaluation_id: string
  source: 'upload' | 'corpus' | 'iot'
  filename?: string | null
  summary: DashboardSummary
  series: SeriesTrust[]
  anomalies: Anomaly[]
  format_ok: boolean
  warnings: string[]
  message: string
  n_suspecte: number
  n_a_verifier: number
  drop_suspects_applied: boolean
  drop_review_applied: boolean
  n_removed: number
  can_export: boolean
}

export interface ActiveDataset {
  evaluationId: string
  filename: string
  dropSuspects: boolean
  dropReview: boolean
  nRemoved: number
  nObservations: number
  trustMedian: number
}

export interface IoTStatus {
  buffer_size: number
  max_points: number
  total_received: number
  last_device_id: string | null
  last_seen_at: string | null
  devices: string[]
  last_reading: Record<string, unknown> | null
  ready_for_evaluation: boolean
  min_recommended: number
}

export interface IoTReading {
  timestamp: string
  station_id: string
  station_name: string
  variable: string
  value: number
  unit: string
  received_at?: string
}

export interface TimePoint {
  timestamp: string
  value: number | null
  qc_status: string
}
