import { useQuery } from '@tanstack/react-query'
import { formatDistanceToNow } from 'date-fns'

interface BondData {
  name: string
  interaction_count: number
  bond_strength: number
  first_contact: string | null
  last_contact: string | null
  relationship: 'new' | 'forming' | 'established' | 'deep'
}

interface BondResponse {
  companion: BondData | null
}

const RELATIONSHIP_STYLES: Record<string, { label: string; color: string; bg: string }> = {
  new: {
    label: 'new',
    color: '#64748b',
    bg: 'rgba(100,116,139,0.12)',
  },
  forming: {
    label: 'forming',
    color: '#22d3ee',
    bg: 'rgba(34,211,238,0.10)',
  },
  established: {
    label: 'established',
    color: '#a78bfa',
    bg: 'rgba(167,139,250,0.12)',
  },
  deep: {
    label: 'deep',
    color: '#fb7185',
    bg: 'rgba(251,113,133,0.12)',
  },
}

function RelationshipBadge({ stage }: { stage: string }) {
  const style = RELATIONSHIP_STYLES[stage] ?? RELATIONSHIP_STYLES.new
  return (
    <span
      className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded border"
      style={{
        color: style.color,
        backgroundColor: style.bg,
        borderColor: style.color + '40',
      }}
    >
      {style.label}
    </span>
  )
}

function BondStrengthBar({ strength }: { strength: number }) {
  const pct = Math.round(strength * 100)
  return (
    <div className="flex items-center gap-2">
      <div
        className="flex-1 h-1 rounded-full overflow-hidden"
        style={{ backgroundColor: 'rgba(251,113,133,0.15)' }}
      >
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{
            width: `${pct}%`,
            backgroundColor: '#fb7185',
            boxShadow: pct > 50 ? '0 0 6px rgba(251,113,133,0.5)' : 'none',
          }}
        />
      </div>
      <span
        className="text-[10px] font-mono shrink-0 tabular-nums"
        style={{ color: '#fb7185' }}
      >
        {pct}%
      </span>
    </div>
  )
}

function formatLastContact(isoString: string | null): string {
  if (!isoString) return 'never'
  try {
    return formatDistanceToNow(new Date(isoString), { addSuffix: true })
  } catch {
    return 'unknown'
  }
}

function BondContent({ companion }: { companion: BondData }) {
  return (
    <div className="space-y-3">
      {/* Name + relationship badge */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {/* Pulsing oxytocin heart dot */}
          <span
            className="w-2 h-2 rounded-full shrink-0"
            style={{
              backgroundColor: '#fb7185',
              boxShadow: '0 0 6px rgba(251,113,133,0.6)',
            }}
          />
          <span className="text-text text-xs font-mono font-semibold">
            {companion.name}
          </span>
        </div>
        <RelationshipBadge stage={companion.relationship} />
      </div>

      {/* Bond strength bar */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <span className="text-text-dim text-[10px] font-mono">bond strength</span>
        </div>
        <BondStrengthBar strength={companion.bond_strength} />
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-1">
        <div>
          <span className="text-text-dim text-[9px] font-mono uppercase tracking-wider opacity-60">
            interactions
          </span>
          <p className="text-text text-xs font-mono font-semibold">
            {companion.interaction_count}
          </p>
        </div>
        <div>
          <span className="text-text-dim text-[9px] font-mono uppercase tracking-wider opacity-60">
            last contact
          </span>
          <p
            className="text-xs font-mono font-semibold truncate"
            style={{ color: companion.last_contact ? '#fb7185' : '#64748b' }}
          >
            {formatLastContact(companion.last_contact)}
          </p>
        </div>
      </div>

      {/* First contact */}
      {companion.first_contact && (
        <div className="border-t border-border pt-2">
          <span className="text-text-dim text-[9px] font-mono uppercase tracking-wider opacity-60">
            first contact
          </span>
          <p className="text-text-dim text-[10px] font-mono mt-0.5">
            {new Date(companion.first_contact).toLocaleDateString(undefined, {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
            })}
          </p>
        </div>
      )}
    </div>
  )
}

export function BondPanel() {
  const { data, isLoading } = useQuery<BondResponse>({
    queryKey: ['social-bond'],
    queryFn: () => fetch('/api/social/bond').then(r => r.json()),
    refetchInterval: 10_000,
  })

  const companion = data?.companion ?? null

  return (
    <div className="border border-border rounded-lg p-3 bg-panel">
      {/* Section header */}
      <div className="flex items-center justify-between mb-3">
        <span
          className="text-text text-[10px] font-mono uppercase tracking-wider font-semibold opacity-70"
          style={{ textShadow: '0 0 8px rgba(251,113,133,0.3)' }}
        >
          companion bond
        </span>
        <span
          className="w-1.5 h-1.5 rounded-full"
          style={{ backgroundColor: '#fb7185', boxShadow: '0 0 4px rgba(251,113,133,0.5)' }}
        />
      </div>

      {isLoading && !companion && (
        <div className="flex items-center justify-center h-16">
          <span className="text-text-dim text-[10px] font-mono animate-pulse opacity-50">
            reading bond…
          </span>
        </div>
      )}

      {!isLoading && !companion && (
        <div className="flex items-center justify-center h-16">
          <span className="text-text-dim text-[10px] font-mono opacity-40">
            no companion data
          </span>
        </div>
      )}

      {companion && <BondContent companion={companion} />}
    </div>
  )
}
