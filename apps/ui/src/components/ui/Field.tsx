import type { InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

interface FieldControlProps {
  id: string
  'aria-describedby'?: string
  'aria-invalid'?: true
}

interface FieldProps {
  id: string
  label: string
  hint?: string
  /** Mensaje de error de validacion (cliente o 422 del servidor). */
  error?: string
  children: (control: FieldControlProps) => ReactNode
}

export function Field({ id, label, hint, error, children }: FieldProps) {
  const hintId = hint ? `${id}-hint` : undefined
  const errorId = error ? `${id}-error` : undefined
  const describedBy = [hintId, errorId].filter(Boolean).join(' ') || undefined

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="font-semibold text-ink">
        {label}
      </label>
      {children({ id, 'aria-describedby': describedBy, 'aria-invalid': error ? true : undefined })}
      {hint && (
        <p id={hintId} className="text-xs text-ink-subtle">
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} role="alert" className="text-xs font-semibold text-status-error-fg">
          {error}
        </p>
      )}
    </div>
  )
}

const control =
  'w-full rounded-lg border border-hairline bg-canvas px-3 py-2 text-ink placeholder:text-slate-400 ' +
  'transition-colors hover:border-slate-300 disabled:cursor-not-allowed disabled:bg-parchment disabled:opacity-60 ' +
  'aria-[invalid=true]:border-status-error-fg'

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(control, className)} {...props} />
}

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cn(control, 'min-h-24 resize-y', className)} {...props} />
}
