import { useSentiaStore } from '../stores/sentiaStore'
import { formatDistanceToNow } from 'date-fns'
import { clsx } from 'clsx'

const THOUGHT_TYPES = new Set(['ThoughtGenerated', 'InsightFormed'])

export function ThoughtStream() {
  const { events } = useSentiaStore()

  const thoughts = events
    .filter(e => THOUGHT_TYPES.has(e.type))
    .slice(0, 8)

  if (thoughts.length === 0) {
    return (
      <p className="text-xs text-text-dim italic font-mono">
        Waiting for first thought...
      </p>
    )
  }

  return (
    <div className="space-y-3">
      {thoughts.map((e) => {
        const content = e.payload?.content as string | undefined
        const isInsight = e.type === 'InsightFormed'
        if (!content) return null
        return (
          <div key={e.id} className="space-y-1">
            <p className={clsx(
              'text-sm leading-relaxed italic',
              isInsight ? 'text-pulse' : 'text-text'
            )}>
              {isInsight && (
                <span className="not-italic text-[10px] font-mono text-pulse/70 mr-1.5 uppercase tracking-wider">
                  insight
                </span>
              )}
              "{content}"
            </p>
            <p className="text-[10px] text-text-dim font-mono">
              {formatDistanceToNow(new Date(e.timestamp), { addSuffix: true })}
            </p>
          </div>
        )
      })}
    </div>
  )
}
