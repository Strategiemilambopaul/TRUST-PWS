import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { SeriesTrust } from '@/types/trust'
import { variableLabel } from '@/utils/format'

export function TrustDistributionChart({ series }: { series: SeriesTrust[] }) {
  const buckets = [
    { key: '0.5-0.7', min: 0.5, max: 0.7 },
    { key: '0.7-0.85', min: 0.7, max: 0.85 },
    { key: '0.85-0.95', min: 0.85, max: 0.95 },
    { key: '0.95-1.0', min: 0.95, max: 1.01 },
  ]

  const data = buckets.map((b) => {
    const row: Record<string, string | number> = { bin: b.key }
    for (const variable of ['temperature', 'humidity', 'pressure']) {
      row[variable] = series.filter(
        (s) => s.variable === variable && s.trust_score >= b.min && s.trust_score < b.max,
      ).length
    }
    return row
  })

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2ddd2" />
          <XAxis dataKey="bin" tick={{ fontSize: 12 }} />
          <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
          <Tooltip
            formatter={(value, name) => [value, variableLabel(String(name))]}
            contentStyle={{ borderRadius: 8, borderColor: '#d7d2c8' }}
          />
          <Bar dataKey="temperature" fill="#2b4c7e" name="temperature" />
          <Bar dataKey="humidity" fill="#1f6f5b" name="humidity" />
          <Bar dataKey="pressure" fill="#b7791f" name="pressure" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
