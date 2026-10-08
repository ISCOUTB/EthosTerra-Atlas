import type { ButtonHTMLAttributes } from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

type Variant = 'primary' | 'secondary' | 'utility'
type Size = 'md' | 'sm'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
}

const variants: Record<Variant, string> = {
  primary: 'rounded-full bg-primary text-white hover:bg-primary-focus',
  secondary: 'rounded-full border border-primary bg-transparent text-primary hover:bg-primary/5',
  utility: 'rounded-lg bg-ink text-white hover:bg-slate-700',
}

const sizes: Record<Size, string> = {
  md: 'min-h-11 px-5.5 py-2.5 text-[17px]',
  sm: 'min-h-8 px-3.5 py-1.5 text-sm',
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  className,
  children,
  type = 'button',
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={cn(
        'inline-flex items-center justify-center gap-2 font-normal transition-[transform,background-color] duration-150',
        'active:scale-95 disabled:cursor-not-allowed disabled:opacity-48 disabled:active:scale-100',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {loading && <Loader2 className="size-4 animate-spin" aria-hidden="true" />}
      {children}
    </button>
  )
}
