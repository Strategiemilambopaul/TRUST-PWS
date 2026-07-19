import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { TimePoint } from '@/types/trust'
import { variableLabel } from '@/utils/format'

export function TimeSeriesChart({
  data,
  variable,
}: {
  data: TimePoint[]
  variable: string
}) {
  const chartData = data.map((d) => ({
    t: d.timestamp.slice(5, 16).replace('T', ' '),
    value: d.value,
    suspect: d.qc_status === 'suspecte' ? d.value : null,
  }))

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2ddd2" />
          <XAxis dataKey="t" minTickGap={40} tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip contentStyle={{ borderRadius: 8, borderColor: '#d7d2c8' }} />
          <Legend />
          <Line
            type="monotone"
            dataKey="value"
            name={variableLabel(variable)}
            stroke="#1f6f5b"
            dot={false}
            strokeWidth={1.8}
          />
          <Line
            type="monotone"
            dataKey="suspect"
            name="Suspecte"
            stroke="#9b2c2c"
            dot={{ r: 2 }}
            strokeWidth={0}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
