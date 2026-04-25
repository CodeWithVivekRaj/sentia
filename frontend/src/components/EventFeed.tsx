import { useSentiaStore } from '../stores/sentiaStore'
import { clsx } from 'clsx'
import { formatDistanceToNow } from 'date-fns'

const EVENT_COLORS: Record<string, string> = {
  AIBorn: 'text-serotonin',
  AIDied: 'text-red-500',
  LLMEnabled: 'text-life',
  LLMDisabled: 'text-text-dim',
  HumanMessageReceived: 'text-endorphin',
  AIResponded: 'text-dopamine',
  ThoughtGenerated: 'text-life',
  EmotionEmerged: 'text-oxytocin',
  NeedCritical: 'text-cortisol',
  DreamOccurred: 'text-melatonin',
  MemoryFormed: 'text-adrenaline',
  SystemStarted: 'text-serotonin',
  SystemStopped: 'text-text-dim',
  ModelChanged: 'text-subtle',
  TickFast: 'text-border',
  TickSlow: 'text-border',
  TickDaily: 'text-subtle',
}

export function EventFeed() {
  const { events } = useSentiaStore()

  const visibleEvents = events.filter(
    e => !['TickFast'].includes(e.type)
  ).slice(0, 30)

  return (
    <div className="space-y-0.5 font-mono text-xs">
      {visibleEvents.length === 0 && (
        <div className="text-text-dim italic py-2">Waiting for events...</div>
      )}
      {visibleEvents.map((e) => (
        <div key={e.id} className="flex items-start gap-2 py-0.5 hover:bg-panel/50 rounded px-1">
          <span className="text-text-dim shrink-0 tabular-nums" style={{ fontSize: '10px' }}>
            {formatDistanceToNow(new Date(e.timestamp), { addSuffix: true })}
          </span>
          <span className={clsx('shrink-0', EVENT_COLORS[e.type] ?? 'text-text-muted')}>
            {e.type}
          </span>
          {e.payload && Object.keys(e.payload).length > 0 && (
            <span className="text-text-dim truncate" style={{ fontSize: '10px' }}>
              {JSON.stringify(e.payload).slice(0, 80)}
            </span>
          )}
        </div>
      ))}
    </div>
  )
}
