import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Card } from '@/components/common/Card'
import { StatTile } from '@/components/common/StatTile'
import { TrustDistributionChart } from '@/components/charts/TrustDistributionChart'
import { fetchDashboard, fetchFfpSummary, fetchSeries } from '@/services/api'
import { formatNumber, formatPercent, formatScore } from '@/utils/format'

export function DashboardPage() {
  const dash = useQuery({ queryKey: ['dashboard'], queryFn: fetchDashboard })
  const series = useQuery({ queryKey: ['series'], queryFn: () => fetchSeries() })
  const ffp = useQuery({ queryKey: ['ffp'], queryFn: fetchFfpSummary })

  if (dash.isLoading) {
    return <p className="text-[var(--color-muted)]">Chargement du tableau de bord…</p>
  }

  if (dash.isError || !dash.data) {
    return (
      <Card title="API indisponible">
        <p className="text-sm text-[var(--color-danger)]">
          Impossible de joindre l’API FastAPI. Lancez{' '}
          <code className="rounded bg-[#ece7dc] px-1">uvicorn app.main:app --reload</code>{' '}
          depuis <code className="rounded bg-[#ece7dc] px-1">App/api</code>.
        </p>
      </Card>
    )
  }

  const s = dash.data

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight">
          Tableau de bord
        </h1>
        <p className="mt-1 max-w-3xl text-sm text-[var(--color-muted)]">
          Vue synthétique du cadre de confiance sur le corpus openSenseMap (T/H/P).
          Les calculs scientifiques restent côté API Python.
        </p>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <StatTile label="Mesures QC" value={formatNumber(s.n_observations)} />
        <StatTile label="Stations" value={formatNumber(s.n_stations)} hint={`${s.n_series} séries`} />
        <StatTile
          label="Score médian"
          value={formatScore(s.trust_score_median)}
          hint={`moyenne ${formatScore(s.trust_score_mean)}`}
          tone="ok"
        />
        <StatTile label="Acceptées (valide)" value={formatNumber(s.n_valide)} tone="ok" />
        <StatTile label="À vérifier" value={formatNumber(s.n_a_verifier)} tone="warn" />
        <StatTile
          label="Suspectes"
          value={formatNumber(s.n_suspecte)}
          hint={`taux anomalies ${formatPercent(s.anomalie_rate)}`}
          tone="danger"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card
          title="Distribution des scores"
          subtitle="Nombre de séries par intervalle de trust_score"
        >
          {series.data ? (
            <TrustDistributionChart series={series.data} />
          ) : (
            <p className="text-sm text-[var(--color-muted)]">Chargement…</p>
          )}
        </Card>

        <Card title="Classes fit-for-purpose" subtitle="Répartition des séries">
          <ul className="space-y-2">
            {(ffp.data ?? []).map((row) => (
              <li
                key={String(row.classe)}
                className="flex items-center justify-between rounded-lg border border-[var(--color-line)] px-3 py-2 text-sm"
              >
                <span>{String(row.classe)}</span>
                <span className="tabular-nums font-medium">
                  {formatNumber(Number(row.n_series))} (
                  {formatPercent(Number(row.proportion))})
                </span>
              </li>
            ))}
          </ul>
          <div className="mt-4 flex flex-wrap gap-2 text-sm">
            <Link className="text-[var(--color-accent)] underline" to="/evaluation">
              Voir le pipeline
            </Link>
            <Link className="text-[var(--color-accent)] underline" to="/anomalies">
              Explorer les anomalies
            </Link>
          </div>
        </Card>
      </div>
    </div>
  )
}
