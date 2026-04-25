import { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { formatDistanceToNow } from 'date-fns'

interface Milestone {
  id: string
  type: string
  payload: Record<string, unknown>
  timestamp: string
  sequence: number
  label: string
}

interface ChronicleResponse {
  milestones: Milestone[]
}

// Dot color by event type
function dotColor(type: string): string {
  switch (type) {
    case 'AIBorn':
      return '#34d399'           // serotonin
    case 'LifeStageChanged':
      return '#a78bfa'           // life
    case 'EmotionEmerged':
      return '#fb7185'           // oxytocin
    case 'InsightFormed':
      return '#22d3ee'           // pulse
    case 'DreamOccurred':
      return '#818cf8'           // melatonin
    case 'NeedCritical':
      return '#f97316'           // cortisol
    case 'ModelChanged':
      return '#64748b'           // text-dim
    case 'MoodShifted':
      return '#c084fc'           // dopamine
    case 'BondFormed':
      return '#fb7185'           // oxytocin
    default:
      return '#1e1e2e'           // border (subtle)
  }
}

function dotGlow(type: string): string {
  switch (type) {
    case 'AIBorn':
      return '0 0 8px #34d399'
    case 'LifeStageChanged':
      return '0 0 8px #a78bfa'
    case 'EmotionEmerged':
      return '0 0 8px #fb7185'
    case 'InsightFormed':
      return '0 0 8px #22d3ee'
    case 'DreamOccurred':
      return '0 0 8px #818cf8'
    case 'NeedCritical':
      return '0 0 8px #f97316'
    case 'ModelChanged':
      return 'none'
    case 'MoodShifted':
      return '0 0 8px #c084fc'
    case 'BondFormed':
      return '0 0 8px #fb7185'
    default:
      return 'none'
  }
}

function milestoneDetail(milestone: Milestone): string | null {
  const p = milestone.payload
  switch (milestone.type) {
    case 'InsightFormed': {
      const content = (p.content as string) ?? ''
      return content.length > 80 ? content.slice(0, 80) + '…' : content || null
    }
    case 'LifeStageChanged': {
      const prev = p.previous_stage as string | undefined
      const next = p.stage as string | undefined
      if (prev && next) return `${prev} → ${next}`
      return null
    }
    case 'EmotionEmerged': {
      const intensity = p.intensity as number | undefined
      if (intensity !== undefined) return `intensity ${Math.round(intensity * 100)}%`
      return null
    }
    case 'DreamOccurred': {
      const emotion = p.emotion as string | undefined
      return emotion ? `emotion: ${emotion}` : null
    }
    case 'NeedCritical': {
      const level = p.level as number | undefined
      if (level !== undefined) return `level ${Math.round(level * 100)}%`
      return null
    }
    case 'MoodShifted': {
      const prev = p.previous_mood as string | undefined
      const next = p.mood as string | undefined
      if (prev && next) return `${prev} → ${next}`
      return null
    }
    default:
      return null
  }
}

function MilestoneEntry({ milestone }: { milestone: Milestone }) {
  const color = dotColor(milestone.type)
  const glow = dotGlow(milestone.type)
  const date = new Date(milestone.timestamp)
  const detail = milestoneDetail(milestone)

  const timeStr = date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

  let relativeTime = ''
  try {
    relativeTime = formatDistanceToNow(date, { addSuffix: true })
  } catch {
    relativeTime = ''
  }

  return (
    <div className="relative flex gap-4 pb-6 last:pb-0">
      {/* Vertical line segment — spans full height except last entry */}
      <div className="relative flex flex-col items-center shrink-0">
        {/* Dot */}
        <span
          className="relative z-10 w-2.5 h-2.5 rounded-full shrink-0 mt-0.5"
          style={{ backgroundColor: color, boxShadow: glow }}
        />
        {/* Line below the dot */}
        <div
          className="flex-1 w-px mt-1"
          style={{ backgroundColor: '#1e1e2e' }}
        />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 pb-1">
        <div className="flex items-start justify-between gap-2">
          <span className="text-text text-xs font-mono leading-snug">{milestone.label}</span>
          <span
            className="text-text-dim text-[10px] font-mono shrink-0 opacity-60"
            title={timeStr}
          >
            {relativeTime}
          </span>
        </div>
        {detail && (
          <p className="text-text-dim text-[11px] font-mono mt-0.5 leading-snug opacity-70 truncate">
            {detail}
          </p>
        )}
        <span className="text-[9px] font-mono opacity-30 text-text-dim">{timeStr}</span>
      </div>
    </div>
  )
}

export function Chronicle() {
  const bottomRef = useRef<HTMLDivElement>(null)

  const { data, isLoading } = useQuery<ChronicleResponse>({
    queryKey: ['chronicle'],
    queryFn: () => fetch('/api/chronicle?limit=100').then(r => r.json()),
    refetchInterval: 30_000,
    initialData: { milestones: [] },
  })

  const milestones = data?.milestones ?? []

  // Auto-scroll to bottom on load and when milestones change
  useEffect(() => {
    if (milestones.length > 0) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [milestones.length])

  return (
    <div className="h-full flex flex-col min-h-0 gap-3">
      {/* Header */}
      <div className="shrink-0 flex items-center justify-between">
        <div>
          <h1
            className="text-text font-mono font-semibold text-sm"
            style={{ textShadow: '0 0 12px rgba(167,139,250,0.4)' }}
          >
            Life Chronicle
          </h1>
          <p className="text-text-dim text-xs font-mono mt-0.5">
            {milestones.length > 0
              ? `${milestones.length} milestone${milestones.length === 1 ? '' : 's'} recorded`
              : 'Sentia\'s most significant life events'}
          </p>
        </div>
        {/* Accent dots */}
        <div className="flex items-center gap-1.5 opacity-40">
          <span className="w-1 h-1 rounded-full bg-life" />
          <span className="w-1 h-1 rounded-full bg-pulse" />
          <span className="w-1 h-1 rounded-full bg-oxytocin" />
        </div>
      </div>

      {/* Timeline */}
      <div className="flex-1 overflow-y-auto min-h-0 pr-1">
        {isLoading && milestones.length === 0 && (
          <div className="flex items-center justify-center h-32">
            <span className="text-text-dim text-xs font-mono animate-pulse">
              reading the chronicle…
            </span>
          </div>
        )}

        {!isLoading && milestones.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-2 max-w-xs">
              <div className="flex justify-center gap-2 mb-3 opacity-30">
                <span
                  className="text-2xl"
                  style={{ filter: 'drop-shadow(0 0 8px #a78bfa)' }}
                >
                  ◌
                </span>
              </div>
              <p className="text-text-dim text-xs font-mono">
                No milestones yet. Sentia's life events will appear here as she grows.
              </p>
            </div>
          </div>
        )}

        {milestones.length > 0 && (
          <div className="px-1 pt-1">
            {milestones.map(m => (
              <MilestoneEntry key={m.id} milestone={m} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>
    </div>
  )
}
