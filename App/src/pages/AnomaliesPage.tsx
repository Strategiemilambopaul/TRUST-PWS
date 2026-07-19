import { useQuery } from '@tanstack/react-query'
import { Card } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'
import { StatusBadge } from '@/components/quality/StatusBadge'
import { fetchAnomalies, fetchStations } from '@/services/api'
import { useAppStore } from '@/store/appStore'
import { variableLabel } from '@/utils/format'

export function AnomaliesPage() {
  const stationId = useAppStore((s) => s.selectedStationId)
  const setStation = useAppStore((s) => s.setStation)
  const stations = useQuery({ queryKey: ['stations'], queryFn: fetchStations })

  const anomalies = useQuery({
    queryKey: ['anomalies', stationId],
    queryFn: () =>
      fetchAnomalies({
        station_id: stationId ?? undefined,
        limit: 250,
      }),
  })

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-[family-name:var(--font-display)] text-3xl font-semibold">
          Détection des anomalies
        </h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Observations <code>suspecte</code> / <code>a_verifier</code> avec types de
          drapeaux (plage physique, figé, saut, MAD, gap…).
        </p>
      </header>

      <Card title="Filtre station">
        <select
          className="w-full max-w-xl rounded-lg border border-[var(--color-line)] bg-white px-3 py-2 text-sm"
          value={stationId ?? ''}
          onChange={(e) => setStation(e.target.value || null)}
        >
          <option value="">Toutes (échantillon)</option>
          {(stations.data ?? []).map((st) => (
            <option key={st.station_id} value={st.station_id}>
              {st.station_name}
            </option>
          ))}
        </select>
      </Card>

      <Card title="Anomalies détectées" subtitle={`${anomalies.data?.length ?? 0} lignes`}>
        <div className="overflow-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-[#f3efe6] text-xs uppercase tracking-wide text-[var(--color-muted)]">
              <tr>
                <th className="px-3 py-2">Station</th>
                <th className="px-3 py-2">Variable</th>
                <th className="px-3 py-2">Horodatage</th>
                <th className="px-3 py-2">Valeur</th>
                <th className="px-3 py-2">Statut</th>
                <th className="px-3 py-2">Types</th>
              </tr>
            </thead>
            <tbody>
              {(anomalies.data ?? []).map((a, i) => (
                <tr key={`${a.timestamp}-${i}`} className="border-t border-[var(--color-line)]">
                  <td className="px-3 py-2">{a.station_name ?? a.station_id}</td>
                  <td className="px-3 py-2">{variableLabel(a.variable)}</td>
                  <td className="px-3 py-2 whitespace-nowrap">{a.timestamp}</td>
                  <td className="px-3 py-2 tabular-nums">{a.value_std ?? '—'}</td>
                  <td className="px-3 py-2">
                    <StatusBadge status={a.qc_status} />
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex flex-wrap gap-1">
                      {a.anomaly_types.map((t) => (
                        <Badge key={t} tone="danger">
                          {t}
                        </Badge>
                      ))}
                    </div>
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
