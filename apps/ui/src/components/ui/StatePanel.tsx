import type { ReactNode } from 'react'
import { AlertCircle, CheckCircle2, Inbox, Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

export type UiState = 'loading' | 'empty' | 'error' | 'success'

interface StatePanelProps {
  state: UiState
  title: string
  description?: string
  /** Accion sugerida: reintentar, crear el primer registro, etc. */
  action?: ReactNode
  className?: string
}

const styles: Record<UiState, string> = {
  loading: 'bg-parchment text-ink-muted',
  empty: 'bg-parchment text-ink-muted',
  error: 'bg-status-error-bg text-status-error-fg',
  success: 'bg-status-puro-bg text-status-puro-fg',
}

function StateIcon({ state }: { state: UiState }) {
  const cls = 'size-5 shrink-0'
  if (state === 'loading') return <Loader2 className={cn(cls, 'animate-spin')} aria-hidden="true" />
  if (state === 'error') return <AlertCircle className={cls} aria-hidden="true" />
  if (state === 'success') return <CheckCircle2 className={cls} aria-hidden="true" />
  return <Inbox className={cls} aria-hidden="true" />
}

export function StatePanel({ state, title, description, action, className }: StatePanelProps) {
  const a11y =
    state === 'error'
      ? ({ role: 'alert' } as const)
      : state === 'loading'
        ? ({ role: 'status', 'aria-busy': true } as const)
        : state === 'success'
          ? ({ role: 'status' } as const)
          : {}

  return (
    <div
      className={cn('flex items-start gap-3 rounded-xl p-6', styles[state], className)}
      {...a11y}
    >
      <StateIcon state={state} />
      <div className="min-w-0 flex-1">
        <p className="font-semibold">{title}</p>
        {description && <p className="mt-1">{description}</p>}
        {action && <div className="mt-4">{action}</div>}
      </div>
    </div>
  )
}
