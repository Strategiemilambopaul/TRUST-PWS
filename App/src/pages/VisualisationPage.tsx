import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card } from '@/components/common/Card'
import { TimeSeriesChart } from '@/components/charts/TimeSeriesChart'
import { StatusBadge } from '@/components/quality/StatusBadge'
import { fetchObservations, fetchStations, fetchTimeseries } from '@/services/api'
import { useAppStore } from '@/store/appStore'
import { variableLabel } from '@/utils/format'

const VARIABLES = ['temperature', 'humidity', 'pressure'] as const

export function VisualisationPage() {
  const stationId = useAppStore((s) => s.selectedStationId)
  const variable = useAppStore((s) => s.selectedVariable)
  const setStation = useAppStore((s) => s.setStation)
  const setVariable = useAppStore((s) => s.setVariable)

  const stations = useQuery({ queryKey: ['stations'], queryFn: fetchStations })

  useEffect(() => {
    if (!stationId && stations.data?.[0]) {
      setStation(stations.data[0].station_id)
    }
  }, [stationId, stations.data, setStation])

  const sid = stationId ?? stations.data?.[0]?.station_id ?? ''

  const ts = useQuery({
    queryKey: ['timeseries', sid, variable],
    queryFn: () => fetchTimeseries(sid, variable, 700),
    enabled: Boolean(sid),
  })

  const obs = useQuery({
    queryKey: ['observations', sid, variable],
    queryFn: () => fetchObservations({ station_id: sid, variable, limit: 80 }),
    enabled: Boolean(sid),
  })

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-[family-name:var(--font-display)] text-3xl font-semibold">
          Visualisation des données
        </h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Corpus mémoire: température, humidité, pression. Vent / précipitations /
          rayonnement hors périmètre (non disponibles ici).
        </p>
      </header>

      <Card title="Filtres">
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-sm">
            Station
            <select
              className="mt-1 w-full rounded-lg border border-[var(--color-line)] bg-white px-3 py-2"
              value={sid}
              onChange={(e) => setStation(e.target.value)}
            >
              {(stations.data ?? []).map((st) => (
                <option key={st.station_id} value={st.station_id}>
                  {st.station_name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            Variable
            <select
              className="mt-1 w-full rounded-lg border border-[var(--color-line)] bg-white px-3 py-2"
              value={variable}
              onChange={(e) => setVariable(e.target.value)}
            >
              {VARIABLES.map((v) => (
                <option key={v} value={v}>
                  {variableLabel(v)}
                </option>
              ))}
            </select>
          </label>
        </div>
      </Card>

      <Card
        title={`Série temporelle · ${variableLabel(variable)}`}
        subtitle="Points rouges: observations suspectes"
      >
        {ts.isLoading && <p className="text-sm text-[var(--color-muted)]">Chargement…</p>}
        {ts.data && <TimeSeriesChart data={ts.data} variable={variable} />}
      </Card>

      <Card title="Tableau d’observations" subtitle="Échantillon récent">
        <div className="overflow-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-[#f3efe6] text-xs uppercase tracking-wide text-[var(--color-muted)]">
              <tr>
                <th className="px-3 py-2">Horodatage</th>
                <th className="px-3 py-2">Valeur</th>
                <th className="px-3 py-2">Unité</th>
                <th className="px-3 py-2">Statut QC</th>
              </tr>
            </thead>
            <tbody>
              {(obs.data ?? []).map((row, i) => (
                <tr key={`${row.timestamp}-${i}`} className="border-t border-[var(--color-line)]">
                  <td className="px-3 py-2 whitespace-nowrap">{row.timestamp}</td>
                  <td className="px-3 py-2 tabular-nums">{row.value_std ?? '—'}</td>
                  <td className="px-3 py-2">{row.unit_std ?? ''}</td>
                  <td className="px-3 py-2">
                    <StatusBadge status={row.qc_status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
