import { useQuery } from '@tanstack/react-query'

// ── Types ────────────────────────────────────────────────────────────────────

interface ChemistryBoost {
  dopamine?: number
  serotonin?: number
  oxytocin?: number
  endorphins?: number
  melatonin?: number
  adrenaline?: number
  cortisol?: number
}

interface RewardDefinition {
  id: string
  name: string
  description: string
  trigger: string
  cooldown_seconds: number
  chemistry_boost?: ChemistryBoost
  _source?: string
}

interface RewardsResponse {
  rewards: RewardDefinition[]
}

// ── Chemistry badge config ───────────────────────────────────────────────────

const CHEM_CONFIG: Record<
  string,
  { label: string; textClass: string; borderClass: string; bgClass: string }
> = {
  dopamine:   { label: 'dopamine',   textClass: 'text-dopamine',   borderClass: 'border-dopamine/30',   bgClass: 'bg-dopamine/5'   },
  serotonin:  { label: 'serotonin',  textClass: 'text-serotonin',  borderClass: 'border-serotonin/30',  bgClass: 'bg-serotonin/5'  },
  oxytocin:   { label: 'oxytocin',   textClass: 'text-oxytocin',   borderClass: 'border-oxytocin/30',   bgClass: 'bg-oxytocin/5'   },
  endorphins: { label: 'endorphins', textClass: 'text-endorphin',  borderClass: 'border-endorphin/30',  bgClass: 'bg-endorphin/5'  },
  melatonin:  { label: 'melatonin',  textClass: 'text-melatonin',  borderClass: 'border-melatonin/30',  bgClass: 'bg-melatonin/5'  },
  adrenaline: { label: 'adrenaline', textClass: 'text-adrenaline', borderClass: 'border-adrenaline/30', bgClass: 'bg-adrenaline/5' },
  cortisol:   { label: 'cortisol',   textClass: 'text-cortisol',   borderClass: 'border-cortisol/30',   bgClass: 'bg-cortisol/5'   },
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatCooldown(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) {
    const m = Math.round(seconds / 60)
    return `${m} min`
  }
  if (seconds < 86400) {
    const h = seconds / 3600
    return `${h % 1 === 0 ? h : h.toFixed(1)} hour${h === 1 ? '' : 's'}`
  }
  const d = seconds / 86400
  return `${d % 1 === 0 ? d : d.toFixed(1)} day${d === 1 ? '' : 's'}`
}

function formatDelta(value: number): string {
  return value >= 0 ? `+${value.toFixed(2)}` : value.toFixed(2)
}

function groupBySource(rewards: RewardDefinition[]): Record<string, RewardDefinition[]> {
  const groups: Record<string, RewardDefinition[]> = {}
  for (const r of rewards) {
    const key = r._source ?? 'other'
    if (!groups[key]) groups[key] = []
    groups[key].push(r)
  }
  return groups
}

function sourceLabel(source: string): string {
  return source.charAt(0).toUpperCase() + source.slice(1)
}

// ── Sub-components ───────────────────────────────────────────────────────────

function ChemBadge({ chem, delta }: { chem: string; delta: number }) {
  const cfg = CHEM_CONFIG[chem]
  if (!cfg) return null
  const isNeg = delta < 0

  return (
    <span
      className={`inline-flex items-center gap-0.5 text-xs font-mono px-1.5 py-0.5 rounded border
        ${cfg.textClass} ${cfg.borderClass} ${cfg.bgClass}
        ${isNeg ? 'opacity-70' : ''}`}
    >
      <span className="opacity-60">{cfg.label}</span>
      <span className="font-semibold">{formatDelta(delta)}</span>
    </span>
  )
}

function TriggerBadge({ trigger }: { trigger: string }) {
  return (
    <span className="inline-block font-mono text-xs px-1.5 py-0.5 rounded border border-pulse/20 bg-pulse/5 text-pulse">
      {trigger}
    </span>
  )
}

function CooldownBadge({ seconds }: { seconds: number }) {
  return (
    <span className="inline-block font-mono text-xs px-1.5 py-0.5 rounded border border-border bg-panel text-text-dim">
      {formatCooldown(seconds)}
    </span>
  )
}

function RewardCard({ reward }: { reward: RewardDefinition }) {
  const boost = reward.chemistry_boost ?? {}
  const chemEntries = Object.entries(boost)

  return (
    <div className="border border-border rounded-lg p-4 bg-panel hover:border-life/20 transition-colors group">
      {/* Name + cooldown row */}
      <div className="flex items-start justify-between gap-3 mb-1.5">
        <span
          className="text-text text-sm font-mono font-semibold group-hover:text-life transition-colors"
          style={{ textShadow: '0 0 12px rgba(167,139,250,0.2)' }}
        >
          {reward.name}
        </span>
        <CooldownBadge seconds={reward.cooldown_seconds} />
      </div>

      {/* Description */}
      <p className="text-text-dim text-xs font-mono mb-3 leading-relaxed">
        {reward.description}
      </p>

      {/* Trigger + chemistry row */}
      <div className="flex flex-wrap items-center gap-1.5">
        <TriggerBadge trigger={reward.trigger} />
        {chemEntries.length > 0 && (
          <span className="text-text-dim text-xs font-mono opacity-40 mx-0.5">→</span>
        )}
        {chemEntries.map(([chem, delta]) => (
          <ChemBadge key={chem} chem={chem} delta={delta} />
        ))}
      </div>
    </div>
  )
}

function GroupSection({
  source,
  rewards,
}: {
  source: string
  rewards: RewardDefinition[]
}) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-text-dim text-xs font-mono uppercase tracking-widest opacity-50">
          {sourceLabel(source)}
        </span>
        <div className="flex-1 h-px bg-border opacity-40" />
        <span className="text-text-dim text-xs font-mono opacity-30">
          {rewards.length} reward{rewards.length !== 1 ? 's' : ''}
        </span>
      </div>
      <div className="space-y-2">
        {rewards.map(r => (
          <RewardCard key={r.id} reward={r} />
        ))}
      </div>
    </div>
  )
}

// ── Page ─────────────────────────────────────────────────────────────────────

export function Rewards() {
  const { data, isLoading } = useQuery<RewardsResponse>({
    queryKey: ['rewards'],
    queryFn: () => fetch('/api/rewards').then(r => r.json()),
    refetchInterval: 60_000,
    initialData: { rewards: [] },
  })

  const rewards = data?.rewards ?? []
  const groups = groupBySource(rewards)
  const sourceOrder = ['social', 'cognitive', ...Object.keys(groups).filter(k => k !== 'social' && k !== 'cognitive')]
  const orderedSources = sourceOrder.filter(s => groups[s]?.length > 0)

  return (
    <div className="h-full flex flex-col min-h-0 gap-3">
      {/* Header */}
      <div className="shrink-0 flex items-center justify-between">
        <div>
          <h1
            className="text-text font-mono font-semibold text-sm"
            style={{ textShadow: '0 0 12px rgba(167,139,250,0.4)' }}
          >
            Reward System
          </h1>
          <p className="text-text-dim text-xs font-mono mt-0.5">
            What Sentia finds meaningful
          </p>
        </div>
        {/* Accent dots */}
        <div className="flex items-center gap-1.5 opacity-40">
          <span className="w-1 h-1 rounded-full bg-dopamine" />
          <span className="w-1 h-1 rounded-full bg-serotonin" />
          <span className="w-1 h-1 rounded-full bg-oxytocin" />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto min-h-0 pr-1">
        {isLoading && rewards.length === 0 && (
          <div className="flex items-center justify-center h-32">
            <span className="text-text-dim text-xs font-mono animate-pulse">
              loading rewards…
            </span>
          </div>
        )}

        {!isLoading && rewards.length === 0 && (
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
                No rewards loaded. Ensure reward definitions exist in the rewards directory.
              </p>
            </div>
          </div>
        )}

        {orderedSources.length > 0 && (
          <div className="space-y-5">
            {orderedSources.map(source => (
              <GroupSection
                key={source}
                source={source}
                rewards={groups[source]}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
