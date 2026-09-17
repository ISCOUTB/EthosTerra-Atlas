import type { FC, ComponentType } from 'react';
import { Eye, Brain, Lightbulb, AlertCircle, HelpCircle, MinusCircle } from 'lucide-react';
import { cn } from '../lib/utils';

export type EpistemicStatus =
  | 'observed'
  | 'inferred'
  | 'proposed'
  | 'required'
  | 'unknown'
  | 'not_stated';

interface EpistemicBadgeProps {
  status: EpistemicStatus;
  label?: string;
  rationale?: string;
  evidenceRef?: string;
  className?: string;
}

const STATUS_CONFIG: Record<
  EpistemicStatus,
  {
    title: string;
    bg: string;
    text: string;
    border: string;
    icon: ComponentType<{ className?: string }>;
  }
> = {
  observed: {
    title: 'Observado',
    bg: 'bg-emerald-50',
    text: 'text-emerald-700',
    border: 'border-emerald-200',
    icon: Eye,
  },
  inferred: {
    title: 'Inferido',
    bg: 'bg-blue-50',
    text: 'text-blue-700',
    border: 'border-blue-200',
    icon: Brain,
  },
  proposed: {
    title: 'Propuesto',
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    border: 'border-amber-200',
    icon: Lightbulb,
  },
  required: {
    title: 'Requerido',
    bg: 'bg-purple-50',
    text: 'text-purple-700',
    border: 'border-purple-200',
    icon: AlertCircle,
  },
  unknown: {
    title: 'Desconocido',
    bg: 'bg-slate-100',
    text: 'text-slate-600',
    border: 'border-slate-300',
    icon: HelpCircle,
  },
  not_stated: {
    title: 'No Declarado',
    bg: 'bg-stone-50',
    text: 'text-stone-600',
    border: 'border-stone-300 border-dashed',
    icon: MinusCircle,
  },
};

export const EpistemicBadge: FC<EpistemicBadgeProps> = ({
  status,
  label,
  rationale,
  evidenceRef,
  className,
}) => {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.unknown;
  const Icon = config.icon;

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border shadow-xs transition-colors',
        config.bg,
        config.text,
        config.border,
        className
      )}
      title={rationale || `Estado epistemológico: ${config.title}`}
    >
      <Icon className="w-3.5 h-3.5 shrink-0" />
      <span>{label || config.title}</span>
      {evidenceRef && (
        <span className="ml-1 text-[10px] opacity-75 font-mono bg-white/70 px-1 py-0.5 rounded border border-current/20">
          {evidenceRef}
        </span>
      )}
    </div>
  );
};
