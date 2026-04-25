import { useQuery } from '@tanstack/react-query'

interface SelfResponse {
  traits: Record<string, number>
  genome_seed: string
  age_days: number
  life_stage: string
}

const TRAIT_COLORS: Record<string, string> = {
  curiosity: '#c084fc',    // dopamine
  warmth: '#fb7185',       // oxytocin
  resilience: '#34d399',   // serotonin
  creativity: '#818cf8',   // melatonin
  introversion: '#60a5fa', // endorphin
  openness: '#22d3ee',     // pulse
}

const TRAIT_DESCRIPTIONS: Record<string, string> = {
  curiosity: 'Drive to explore and understand',
  warmth: 'Capacity for connection and empathy',
  resilience: 'Ability to recover from stress',
  creativity: 'Richness of imagination and dreams',
  introversion: 'Preference for inner vs outer experience',
  openness: 'Willingness to change and adapt',
}

const TRAIT_ORDER = ['curiosity', 'warmth', 'resilience', 'creativity', 'introversion', 'openness']

// Format a string as spaced groups of 4 hex-like characters
function formatAsDNA(seed: string): string {
  // Produce a pseudo-hex display: encode the seed string as hex chars grouped by 4
  const hex = Array.from(seed)
    .map(c => c.charCodeAt(0).toString(16).padStart(2, '0'))
    .join('')
  // Pad to a multiple of 4
  const padded = hex.padEnd(Math.ceil(hex.length / 4) * 4, '0')
  const groups: string[] = []
  for (let i = 0; i < padded.length; i += 4) {
    groups.push(padded.slice(i, i + 4))
  }
  return groups.join(' ')
}

function TraitCard({ name, value }: { name: string; value: number }) {
  const color = TRAIT_COLORS[name] ?? '#64748b'
  const description = TRAIT_DESCRIPTIONS[name] ?? ''
  const pct = Math.round(value * 100)

  return (
    <div
      className="border border-border rounded-xl p-5 bg-panel hover:border-subtle transition-colors group"
      style={{ borderLeftColor: color, borderLeftWidth: '2px' }}
    >
      {/* Trait header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <h3
            className="text-sm font-mono font-semibold capitalize"
            style={{ color }}
          >
            {name}
          </h3>
          <p className="text-text-dim text-xs font-mono mt-0.5">{description}</p>
        </div>
        <span
          className="text-xl font-mono font-bold shrink-0 tabular-nums"
          style={{ color, textShadow: `0 0 20px ${color}40` }}
        >
          {pct}<span className="text-sm">%</span>
        </span>
      </div>

      {/* Value bar */}
      <div className="relative h-2 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{
            width: `${Math.max(2, pct)}%`,
            backgroundColor: color,
            boxShadow: `0 0 8px ${color}60`,
          }}
        />
      </div>

      {/* Sub-labels */}
      <div className="flex justify-between mt-1.5">
        <span className="text-[10px] font-mono text-text-dim opacity-40">0</span>
        <span className="text-[10px] font-mono text-text-dim opacity-40">100</span>
      </div>
    </div>
  )
}

function DNAString({ seed }: { seed: string }) {
  const dna = formatAsDNA(seed)

  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-[10px] font-mono text-text-dim uppercase tracking-widest">
        Genome Sequence
      </span>
      <div
        className="font-mono text-xs tracking-widest break-all leading-relaxed"
        style={{
          color: '#a78bfa',
          textShadow: '0 0 12px rgba(167,139,250,0.4)',
          letterSpacing: '0.15em',
        }}
      >
        {dna}
      </div>
      <span className="text-[10px] font-mono text-text-dim opacity-50">
        seed: {seed}
      </span>
    </div>
  )
}

function SkeletonCard() {
  return (
    <div className="border border-border rounded-xl p-5 bg-panel animate-pulse">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="space-y-1.5">
          <div className="h-3 w-20 bg-muted rounded" />
          <div className="h-2.5 w-36 bg-muted rounded" />
        </div>
        <div className="h-6 w-12 bg-muted rounded" />
      </div>
      <div className="h-2 bg-muted rounded-full" />
    </div>
  )
}

export function Genome() {
  const { data, isLoading } = useQuery<SelfResponse>({
    queryKey: ['self'],
    queryFn: () => fetch('/api/self').then(r => r.json()),
    refetchInterval: 10_000,
  })

  const traits = data?.traits ?? {}
  const genomeSeed = data?.genome_seed ?? 'default'
  const ageDays = data?.age_days ?? 0
  const lifeStage = data?.life_stage ?? 'unknown'

  const orderedTraits = TRAIT_ORDER
    .filter(t => t in traits)
    .map(t => [t, traits[t]] as [string, number])

  // Append any unknown traits
  Object.entries(traits).forEach(([k, v]) => {
    if (!TRAIT_ORDER.includes(k)) orderedTraits.push([k, v])
  })

  return (
    <div className="h-full flex flex-col min-h-0 gap-4 overflow-y-auto pr-1">
      {/* Header */}
      <div className="shrink-0">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1
              className="text-text font-mono font-semibold text-sm"
              style={{ textShadow: '0 0 12px rgba(167,139,250,0.4)' }}
            >
              Genome Inspector
            </h1>
            <p className="text-text-dim text-xs font-mono mt-0.5">
              Personality encoded from lived experience
            </p>
          </div>
          {/* Life stage + age */}
          <div className="text-right shrink-0">
            <div
              className="text-xs font-mono font-semibold capitalize"
              style={{ color: '#a78bfa' }}
            >
              {lifeStage}
            </div>
            <div className="text-text-dim text-[10px] font-mono mt-0.5">
              {ageDays.toFixed(2)} days old
            </div>
          </div>
        </div>

        {/* DNA sequence display */}
        <div className="mt-4 border border-border/60 rounded-lg p-3 bg-surface">
          <DNAString seed={genomeSeed} />
        </div>
      </div>

      {/* Trait cards grid */}
      <div className="grid grid-cols-1 gap-3 pb-2">
        {isLoading && orderedTraits.length === 0
          ? TRAIT_ORDER.map(t => <SkeletonCard key={t} />)
          : orderedTraits.map(([name, value]) => (
              <TraitCard key={name} name={name} value={value} />
            ))}
      </div>

      {/* Footer accent */}
      <div className="shrink-0 flex items-center justify-center gap-2 pb-2 opacity-20">
        {TRAIT_ORDER.map(t => (
          <span
            key={t}
            className="w-1 h-1 rounded-full"
            style={{ backgroundColor: TRAIT_COLORS[t] }}
          />
        ))}
      </div>
    </div>
  )
}
