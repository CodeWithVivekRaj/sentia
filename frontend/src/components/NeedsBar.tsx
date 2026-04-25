import { clsx } from 'clsx'

const NEED_COLORS: Record<string, string> = {
  energy: 'bg-adrenaline',
  stimulation: 'bg-dopamine',
  connection: 'bg-oxytocin',
  safety: 'bg-serotonin',
  purpose: 'bg-life',
  rest: 'bg-melatonin',
}

interface Props {
  needs: Record<string, number>
}

export function NeedsBar({ needs }: Props) {
  return (
    <div className="space-y-2">
      {Object.entries(needs).map(([name, value]) => (
        <div key={name} className="flex items-center gap-3">
          <span className="text-xs font-mono text-text-dim w-20 capitalize">{name}</span>
          <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
            <div
              className={clsx(
                'h-full rounded-full transition-all duration-700',
                NEED_COLORS[name] ?? 'bg-subtle',
                value < 0.2 && 'animate-pulse'
              )}
              style={{ width: `${Math.max(2, value * 100)}%` }}
            />
          </div>
          <span className={clsx(
            'text-xs font-mono w-8 text-right',
            value < 0.2 ? 'text-cortisol' : value < 0.5 ? 'text-adrenaline' : 'text-text-dim'
          )}>
            {Math.round(value * 100)}
          </span>
        </div>
      ))}
    </div>
  )
}
