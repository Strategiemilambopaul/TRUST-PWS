import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'
import { RadarDimensions } from '@/components/charts/RadarDimensions'
import { fetchSeries } from '@/services/api'
import { formatPercent, formatScore, variableLabel } from '@/utils/format'

function levelFromScore(score: number) {
  if (score >= 0.85) return { label: 'Élevé', tone: 'ok' as const }
  if (score >= 0.65) return { label: 'Moyen', tone: 'warn' as const }
  return { label: 'Faible', tone: 'danger' as const }
}

export function ScorePage() {
  const series = useQuery({ queryKey: ['series'], queryFn: () => fetchSeries() })
  const [key, setKey] = useState<string>('')

  const options = useMemo(() => {
    return (series.data ?? []).map(
      (s) => `${s.station_id}::${s.variable}::${s.station_name}`,
    )
  }, [series.data])

  const selected = useMemo(() => {
    const k = key || options[0] || ''
    const [station_id, variable] = k.split('::')
    return (series.data ?? []).find(
      (s) => s.station_id === station_id && s.variable === variable,
    )
  }, [key, options, series.data])

  const level = selected ? levelFromScore(selected.trust_score) : null

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-[family-name:var(--font-display)] text-3xl font-semibold">
          Score de confiance
        </h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Score global, dimensions et classe d’usage pour une série station–variable.
        </p>
      </header>

      <Card title="Série">
        <select
          className="w-full rounded-lg border border-[var(--color-line)] bg-white px-3 py-2 text-sm"
          value={key || options[0] || ''}
          onChange={(e) => setKey(e.target.value)}
        >
          {options.map((opt) => {
            const [, variable, name] = opt.split('::')
            return (
              <option key={opt} value={opt}>
                {name} · {variableLabel(variable)}
              </option>
            )
          })}
        </select>
      </Card>

      {selected && level && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card title="Score global" subtitle={selected.station_name}>
            <p className="font-[family-name:var(--font-display)] text-5xl font-semibold tabular-nums text-[var(--color-accent)]">
              {formatScore(selected.trust_score)}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Badge tone={level.tone}>Niveau {level.label}</Badge>
              <Badge tone="accent">{selected.fit_for_purpose}</Badge>
              <Badge tone="neutral">{variableLabel(selected.variable)}</Badge>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-[var(--color-muted)]">
              Justification: moyenne pondérée des dimensions (complétude 0,20,
              physique 0,25, stabilité 0,20, statistique 0,15, continuité 0,10,
              métadonnées 0,05). Spatial désactivé. Ce score mesure une confiance
              relative, pas une exactitude métrologique.
            </p>
          </Card>

          <Card title="Radar des dimensions">
            <RadarDimensions series={selected} />
          </Card>

          <Card title="Détail des dimensions" className="lg:col-span-2">
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {[
                ['Complétude', selected.dim_completeness],
                ['Physique', selected.dim_physical],
                ['Stabilité', selected.dim_stability],
                ['Statistique', selected.dim_statistical],
                ['Continuité', selected.dim_continuity],
                ['Métadonnées', selected.dim_metadata],
              ].map(([label, value]) => (
                <div
                  key={String(label)}
                  className="rounded-lg border border-[var(--color-line)] px-3 py-2"
                >
                  <p className="text-xs text-[var(--color-muted)]">{label}</p>
                  <p className="text-lg font-semibold tabular-nums">
                    {formatScore(Number(value))}
                  </p>
                </div>
              ))}
            </div>
            <p className="mt-4 text-sm text-[var(--color-muted)]">
              Taux suspect: {formatPercent(selected.suspect_observation_rate)} · figé:{' '}
              {formatPercent(selected.stuck_value_rate)} · sauts:{' '}
              {formatPercent(selected.temporal_jump_rate)}
            </p>
          </Card>
        </div>
      )}
    </div>
  )
}
