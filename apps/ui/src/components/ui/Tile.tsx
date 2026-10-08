import type { HTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

type Tone = 'light' | 'parchment' | 'dark'

interface TileProps extends HTMLAttributes<HTMLElement> {
  tone?: Tone
}

const tones: Record<Tone, string> = {
  light: 'bg-canvas text-ink',
  parchment: 'bg-parchment text-ink',
  dark: 'bg-tile-dark text-white',
}

export function Tile({ tone = 'light', className, children, ...props }: TileProps) {
  return (
    <section className={cn('py-8 md:py-12', tones[tone], className)} {...props}>
      <div className="mx-auto w-full max-w-360 px-4 md:px-6">{children}</div>
    </section>
  )
}
