import type { HTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

export type BadgeTone =
  | 'puro'
  | 'conflictivo'
  | 'error'
  | 'vencido'
  | 'restaurado'
  | 'neutral'

const tones: Record<BadgeTone, string> = {
  puro: 'bg-status-puro-bg text-status-puro-fg',
  conflictivo: 'bg-status-conflictivo-bg text-status-conflictivo-fg',
  error: 'bg-status-error-bg text-status-error-fg',
  vencido: 'bg-status-vencido-bg text-status-vencido-fg',
  restaurado: 'bg-status-restaurado-bg text-status-restaurado-fg',
  neutral: 'bg-parchment text-ink-muted',
}

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone
}

export function Badge({ tone = 'neutral', className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold',
        tones[tone],
        className,
      )}
      {...props}
    />
  )
}
