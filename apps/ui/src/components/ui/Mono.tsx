import type { HTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

export function Mono({ className, ...props }: HTMLAttributes<HTMLElement>) {
  return <code className={cn('font-mono break-all text-ink', className)} {...props} />
}
