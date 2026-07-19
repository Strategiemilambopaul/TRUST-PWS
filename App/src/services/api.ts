import axios from 'axios'
import type {
  Anomaly,
  DashboardSummary,
  EvaluateResult,
  HistoryItem,
  ImportPreview,
  IoTReading,
  IoTStatus,
  Observation,
  PipelineStep,
  SeriesTrust,
  Station,
  TimePoint,
} from '@/types/trust'

const api = axios.create({
  baseURL: '/api',
  timeout: 120_000,
})

export async function fetchHealth() {
  const { data } = await api.get('/health')
  return data as { status: string; metrics_exists: boolean }
}

export async function fetchDashboard() {
  const { data } = await api.get<DashboardSummary>('/dashboard/summary')
  return data
}

export async function fetchStations() {
  const { data } = await api.get<Station[]>('/stations')
  return data
}

export async function fetchSeries(params?: { station_id?: string; variable?: string }) {
  const { data } = await api.get<SeriesTrust[]>('/series', { params })
  return data
}

export async function fetchObservations(params: {
  station_id?: string
  variable?: string
  limit?: number
}) {
  const { data } = await api.get<Observation[]>('/observations', { params })
  return data
}

export async function fetchTimeseries(station_id: string, variable: string, limit = 800) {
  const { data } = await api.get<TimePoint[]>('/timeseries', {
    params: { station_id, variable, limit },
  })
  return data
}

export async function fetchAnomalies(params?: {
  station_id?: string
  variable?: string
  limit?: number
}) {
  const { data } = await api.get<Anomaly[]>('/anomalies', { params })
  return data
}

export async function fetchPipelineSteps() {
  const { data } = await api.get<PipelineStep[]>('/pipeline/steps')
  return data
}

export async function fetchFfpSummary() {
  const { data } = await api.get<Record<string, unknown>[]>('/trust/ffp-summary')
  return data
}

export async function fetchHistory(limit = 40) {
  const { data } = await api.get<HistoryItem[]>('/history', { params: { limit } })
  return data
}

export async function previewImport(file: File) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post<ImportPreview>('/import/preview', form)
  return data
}

export async function runEvaluate(file?: File) {
  const form = new FormData()
  if (file) form.append('file', file)
  const { data } = await api.post<EvaluateResult>('/evaluate', form)
  return data
}

export async function cleanEvaluation(
  evaluationId: string,
  opts: { drop_suspects?: boolean; drop_review?: boolean } = {},
) {
  const { data } = await api.post<EvaluateResult>(`/evaluate/${evaluationId}/clean`, {
    drop_suspects: opts.drop_suspects ?? true,
    drop_review: opts.drop_review ?? false,
  })
  return data
}

export async function downloadEvaluationExport(
  evaluationId: string,
  opts: { drop_suspects?: boolean; drop_review?: boolean } = {},
) {
  const { data } = await api.get<Blob>(`/evaluate/${evaluationId}/export`, {
    params: {
      drop_suspects: opts.drop_suspects ?? false,
      drop_review: opts.drop_review ?? false,
    },
    responseType: 'blob',
  })
  return data
}

export async function fetchIoTStatus() {
  const { data } = await api.get<IoTStatus>('/iot/status')
  return data
}

export async function fetchIoTReadings(limit = 80) {
  const { data } = await api.get<IoTReading[]>('/iot/readings', { params: { limit } })
  return data
}

export async function evaluateIoTBuffer() {
  const { data } = await api.post<EvaluateResult>('/iot/evaluate')
  return data
}

export async function clearIoTBuffer() {
  const { data } = await api.delete<{ cleared: boolean; buffer_size: number }>('/iot/buffer')
  return data
}

export async function simulateIoT(n = 30) {
  const { data } = await api.post<{ accepted: number; buffer_size: number; device_id: string }>(
    '/iot/simulate',
    null,
    { params: { n } },
  )
  return data
}

export async function ingestIoTManual(payload: {
  device_id: string
  temperature?: number
  humidity?: number
  pressure?: number
}) {
  const { data } = await api.post('/iot/ingest', payload)
  return data
}
