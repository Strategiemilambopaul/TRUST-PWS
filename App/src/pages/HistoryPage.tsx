import { useQuery } from '@tanstack/react-query'
import { Card } from '@/components/common/Card'
import { StatusBadge } from '@/components/quality/StatusBadge'
import { fetchHistory } from '@/services/api'
import { formatNumber, formatScore } from '@/utils/format'

export function HistoryPage() {
  const history = useQuery({
    queryKey: ['history'],
    queryFn: () => fetchHistory(40),
  })

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-[family-name:var(--font-display)] text-3xl font-semibold">
          Historique des évaluations
        </h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Synthèse par station à partir des scores déjà calculés du corpus mémoire.
        </p>
      </header>

      <Card title="Évaluations" subtitle={`${history.data?.length ?? 0} stations`}>
        <div className="overflow-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-[#f3efe6] text-xs uppercase tracking-wide text-[var(--color-muted)]">
              <tr>
                <th className="px-3 py-2">Date</th>
                <th className="px-3 py-2">Station</th>
                <th className="px-3 py-2">Score</th>
                <th className="px-3 py-2">Niveau</th>
                <th className="px-3 py-2">Classe FFP</th>
                <th className="px-3 py-2">Anomalies (approx.)</th>
                <th className="px-3 py-2">Résumé</th>
              </tr>
            </thead>
            <tbody>
              {(history.data ?? []).map((h) => (
                <tr key={h.id} className="border-t border-[var(--color-line)]">
                  <td className="px-3 py-2 whitespace-nowrap">{h.date}</td>
                  <td className="px-3 py-2">{h.station_name}</td>
                  <td className="px-3 py-2 tabular-nums font-medium">
                    {formatScore(h.trust_score)}
                  </td>
                  <td className="px-3 py-2">
                    <StatusBadge status={h.status} />
                  </td>
                  <td className="px-3 py-2 text-xs">{h.fit_for_purpose}</td>
                  <td className="px-3 py-2 tabular-nums">{formatNumber(h.n_anomalies)}</td>
                  <td className="px-3 py-2 text-xs text-[var(--color-muted)]">{h.summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
