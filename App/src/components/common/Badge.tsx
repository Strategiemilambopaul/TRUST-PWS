import type { ReactNode } from 'react'
import { cn } from '@/utils/cn'

export function Badge({
  children,
  tone = 'neutral',
  className,
}: {
  children: ReactNode
  tone?: 'neutral' | 'ok' | 'warn' | 'danger' | 'accent'
  className?: string
}) {
  const tones = {
    neutral: 'bg-[#ece7dc] text-[var(--color-ink)]',
    ok: 'bg-[#dcfce7] text-[var(--color-ok)]',
    warn: 'bg-[#fef3c7] text-[var(--color-warn)]',
    danger: 'bg-[#fee2e2] text-[var(--color-danger)]',
    accent: 'bg-[var(--color-accent-soft)] text-[var(--color-accent)]',
  }
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium',
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  )
}
