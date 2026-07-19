import type { ReactNode } from 'react'
import { X } from 'lucide-react'
import { cn } from '@/utils/cn'

export function Modal({
  open,
  title,
  children,
  onClose,
  tone = 'danger',
  footer,
  closeOnBackdrop = true,
}: {
  open: boolean
  title: string
  children: ReactNode
  onClose: () => void
  tone?: 'danger' | 'warn' | 'neutral'
  footer?: ReactNode
  closeOnBackdrop?: boolean
}) {
  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#122028]/55 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      onClick={closeOnBackdrop ? onClose : undefined}
    >
      <div
        className="w-full max-w-lg rounded-xl border border-[var(--color-line)] bg-[var(--color-paper)] shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3 border-b border-[var(--color-line)] px-5 py-4">
          <h2
            id="modal-title"
            className={cn(
              'font-[family-name:var(--font-display)] text-lg font-semibold',
              tone === 'danger' && 'text-[var(--color-danger)]',
              tone === 'warn' && 'text-[var(--color-warn)]',
            )}
          >
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-[var(--color-muted)] hover:bg-[#f3efe6]"
            aria-label="Fermer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="px-5 py-4 text-sm leading-relaxed text-[var(--color-ink)]">
          {children}
        </div>
        <div className="flex flex-wrap justify-end gap-2 border-t border-[var(--color-line)] px-5 py-3">
          {footer ?? (
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white"
            >
              Compris
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
