import { ShieldCheck, Cpu, Terminal } from 'lucide-react'

export function GlobalNav() {
  return (
    <div className="bg-slate-950/95 border-b border-white/10 text-white backdrop-blur-md">
      <div className="mx-auto flex h-11 w-full max-w-360 items-center justify-between px-4 md:px-6 text-xs">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Terminal className="size-3.5 text-blue-400" aria-hidden="true" />
            <span className="font-semibold tracking-tight text-slate-100">EthosTerra Knowledge Studio</span>
          </div>
          <span className="hidden text-slate-400 sm:inline">·</span>
          <span className="hidden text-slate-400 font-medium sm:inline">Laboratorio eBDI & Clasificador Territorial</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-slate-900 border border-slate-800 text-[11px] text-slate-300">
            <Cpu className="size-3 text-indigo-400" aria-hidden="true" />
            <span>ai/gemma4:E4B</span>
          </div>
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-800/60 text-[11px] font-medium text-emerald-300">
            <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <ShieldCheck className="size-3" aria-hidden="true" />
            Offline-First Soberano
          </span>
        </div>
      </div>
    </div>
  )
}
