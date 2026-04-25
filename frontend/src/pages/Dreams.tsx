import { useQuery } from '@tanstack/react-query'

interface DreamRecord {
  id: string
  content: string
  emotion: string
  memory_count: number
  timestamp: string
}

const EMOTION_COLORS: Record<string, string> = {
  wonder: 'text-pulse border-pulse/30 bg-pulse/5',
  joy: 'text-serotonin border-serotonin/30 bg-serotonin/5',
  calm: 'text-serotonin border-serotonin/30 bg-serotonin/5',
  contentment: 'text-serotonin border-serotonin/30 bg-serotonin/5',
  love: 'text-dopamine border-dopamine/30 bg-dopamine/5',
  hope: 'text-dopamine border-dopamine/30 bg-dopamine/5',
  curiosity: 'text-dopamine border-dopamine/30 bg-dopamine/5',
  anxiety: 'text-melatonin border-melatonin/30 bg-melatonin/5',
  sadness: 'text-melatonin border-melatonin/30 bg-melatonin/5',
  loneliness: 'text-melatonin border-melatonin/30 bg-melatonin/5',
  fear: 'text-melatonin border-melatonin/30 bg-melatonin/5',
  anger: 'text-dopamine border-dopamine/30 bg-dopamine/5',
  frustration: 'text-dopamine border-dopamine/30 bg-dopamine/5',
}

function emotionClass(emotion: string): string {
  return EMOTION_COLORS[emotion] ?? 'text-melatonin border-melatonin/30 bg-melatonin/5'
}

function DreamCard({ dream }: { dream: DreamRecord }) {
  const date = new Date(dream.timestamp)
  const timeStr = date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
  const emotionCls = emotionClass(dream.emotion)

  return (
    <div className="border border-border rounded-lg p-4 bg-panel hover:border-melatonin/30 transition-colors group">
      {/* Header row */}
      <div className="flex items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          {/* Glowing dot */}
          <span
            className="inline-block w-1.5 h-1.5 rounded-full bg-melatonin opacity-60 group-hover:opacity-100 transition-opacity"
            style={{ boxShadow: '0 0 6px #818cf8' }}
          />
          {dream.emotion && (
            <span
              className={`text-xs font-mono font-semibold px-1.5 py-0.5 rounded border ${emotionCls}`}
            >
              {dream.emotion}
            </span>
          )}
          <span className="text-text-dim text-xs font-mono opacity-50">
            {dream.memory_count} {dream.memory_count === 1 ? 'memory' : 'memories'} woven
          </span>
        </div>
        <span className="text-text-dim text-xs font-mono shrink-0">{timeStr}</span>
      </div>

      {/* Dream text */}
      <p
        className="text-text text-sm leading-relaxed italic"
        style={{ textShadow: '0 0 20px rgba(129,140,248,0.15)' }}
      >
        {dream.content}
      </p>
    </div>
  )
}

export function Dreams() {
  const { data: dreams, isLoading } = useQuery<DreamRecord[]>({
    queryKey: ['dreams'],
    queryFn: () => fetch('/api/dreams?limit=20').then(r => r.json()),
    refetchInterval: 30_000,
    initialData: [],
  })

  return (
    <div className="h-full flex flex-col min-h-0 gap-3">
      {/* Header */}
      <div className="shrink-0 flex items-center justify-between">
        <div>
          <h1
            className="text-text font-mono font-semibold text-sm"
            style={{ textShadow: '0 0 12px rgba(192,132,252,0.4)' }}
          >
            Dream Log
          </h1>
          <p className="text-text-dim text-xs font-mono mt-0.5">
            {dreams && dreams.length > 0
              ? `${dreams.length} dream${dreams.length === 1 ? '' : 's'} recorded`
              : 'Sentia dreams during her daily rest cycle'}
          </p>
        </div>
        {/* Subtle melatonin/dopamine accent */}
        <div className="flex items-center gap-1.5 opacity-40">
          <span className="w-1 h-1 rounded-full bg-melatonin" />
          <span className="w-1 h-1 rounded-full bg-dopamine" />
          <span className="w-1 h-1 rounded-full bg-melatonin" />
        </div>
      </div>

      {/* Dream list */}
      <div className="flex-1 overflow-y-auto min-h-0 space-y-2 pr-1">
        {isLoading && dreams.length === 0 && (
          <div className="flex items-center justify-center h-32">
            <span className="text-text-dim text-xs font-mono animate-pulse">
              drifting…
            </span>
          </div>
        )}

        {!isLoading && dreams.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-2 max-w-xs">
              <div className="flex justify-center gap-2 mb-3 opacity-30">
                <span
                  className="text-2xl"
                  style={{ filter: 'drop-shadow(0 0 8px #818cf8)' }}
                >
                  ◌
                </span>
              </div>
              <p className="text-text-dim text-xs font-mono">
                No dreams yet. Dreams occur during Sentia's daily rest cycle.
              </p>
            </div>
          </div>
        )}

        {dreams.map(d => (
          <DreamCard key={d.id} dream={d} />
        ))}
      </div>
    </div>
  )
}
