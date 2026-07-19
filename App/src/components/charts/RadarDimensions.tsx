import {
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import type { SeriesTrust } from '@/types/trust'

export function RadarDimensions({ series }: { series: SeriesTrust | null }) {
  if (!series) {
    return (
      <p className="text-sm text-[var(--color-muted)]">
        Sélectionnez une série pour afficher le radar des dimensions.
      </p>
    )
  }

  const data = [
    { dim: 'Complétude', value: series.dim_completeness },
    { dim: 'Physique', value: series.dim_physical },
    { dim: 'Stabilité', value: series.dim_stability },
    { dim: 'Statistique', value: series.dim_statistical },
    { dim: 'Continuité', value: series.dim_continuity },
    { dim: 'Métadonnées', value: series.dim_metadata },
  ]

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer>
        <RadarChart data={data}>
          <PolarGrid stroke="#d7d2c8" />
          <PolarAngleAxis dataKey="dim" tick={{ fontSize: 11 }} />
          <PolarRadiusAxis domain={[0, 1]} tick={{ fontSize: 10 }} />
          <Tooltip />
          <Legend />
          <Radar
            name="Dimensions"
            dataKey="value"
            stroke="#2b4c7e"
            fill="#2b4c7e"
            fillOpacity={0.35}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
