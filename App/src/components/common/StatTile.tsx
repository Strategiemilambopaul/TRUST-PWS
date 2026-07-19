import { Card } from '@/components/common/Card'
import { cn } from '@/utils/cn'

export function StatTile({
  label,
  value,
  hint,
  tone = 'default',
}: {
  label: string
  value: string
  hint?: string
  tone?: 'default' | 'ok' | 'warn' | 'danger'
}) {
  return (
    <Card className="overflow-hidden">
      <p className="text-xs font-medium uppercase tracking-[0.08em] text-[var(--color-muted)]">
        {label}
      </p>
      <p
        className={cn(
          'mt-2 font-[family-name:var(--font-display)] text-2xl font-semibold tabular-nums',
          tone === 'ok' && 'text-[var(--color-ok)]',
          tone === 'warn' && 'text-[var(--color-warn)]',
          tone === 'danger' && 'text-[var(--color-danger)]',
        )}
      >
        {value}
      </p>
      {hint && <p className="mt-1 text-xs text-[var(--color-muted)]">{hint}</p>}
    </Card>
  )
}
