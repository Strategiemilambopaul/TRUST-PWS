import type { ReactNode } from 'react'
import { cn } from '@/utils/cn'

export function Card({
  children,
  className,
  title,
  subtitle,
  action,
}: {
  children: ReactNode
  className?: string
  title?: string
  subtitle?: string
  action?: ReactNode
}) {
  return (
    <section
      className={cn(
        'rounded-xl border border-[var(--color-line)] bg-[var(--color-panel)] shadow-[0_1px_0_rgba(20,33,43,0.04)]',
        className,
      )}
    >
      {(title || action) && (
        <header className="flex items-start justify-between gap-3 border-b border-[var(--color-line)] px-4 py-3">
          <div>
            {title && (
              <h2 className="font-[family-name:var(--font-display)] text-lg font-semibold tracking-tight">
                {title}
              </h2>
            )}
            {subtitle && <p className="mt-0.5 text-sm text-[var(--color-muted)]">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  )
}
