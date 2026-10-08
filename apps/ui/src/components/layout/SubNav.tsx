import type { ComponentType } from 'react'
import { cn } from '../../lib/utils'

export interface NavItem<Id extends string> {
  id: Id
  label: string
  icon: ComponentType<{ className?: string; 'aria-hidden'?: boolean | 'true' }>
}

interface SubNavProps<Id extends string> {
  items: NavItem<Id>[]
  active: Id
  onSelect: (id: Id) => void
}

export function SubNav<Id extends string>({ items, active, onSelect }: SubNavProps<Id>) {
  const current = items.find((item) => item.id === active)

  return (
    <div className="border-b border-slate-200/80 bg-white/80 backdrop-blur-xl shadow-xs">
      <div className="mx-auto flex min-h-14 w-full max-w-360 flex-wrap items-center justify-between gap-x-6 gap-y-2 px-4 py-2 md:px-6">
        <div className="flex items-center gap-2.5">
          <span className="size-2 rounded-full bg-blue-600" />
          <h1 className="text-lg leading-tight font-bold tracking-tight text-slate-900">
            {current?.label}
          </h1>
        </div>
        <nav aria-label="Módulos" className="-mx-1 overflow-x-auto">
          <ul className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-100/80 border border-slate-200/60">
            {items.map(({ id, label, icon: Icon }) => {
              const isActive = id === active
              return (
                <li key={id}>
                  <button
                    type="button"
                    onClick={() => onSelect(id)}
                    aria-current={isActive ? 'page' : undefined}
                    className={cn(
                      'flex min-h-9 items-center gap-2 whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-semibold transition-all duration-150',
                      isActive
                        ? 'bg-white text-slate-900 shadow-xs ring-1 ring-black/5'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-white/50',
                    )}
                  >
                    <Icon className={cn('size-3.5 transition-colors', isActive ? 'text-blue-600' : 'text-slate-400')} aria-hidden="true" />
                    <span>{label}</span>
                  </button>
                </li>
              )
            })}
          </ul>
        </nav>
      </div>
    </div>
  )
}
