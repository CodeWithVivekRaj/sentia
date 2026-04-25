import { useQuery } from '@tanstack/react-query'

const TRAIT_COLORS: Record<string, string> = {
  curiosity: '#c084fc',    // dopamine
  warmth: '#fb7185',       // oxytocin
  resilience: '#34d399',   // serotonin
  creativity: '#818cf8',   // melatonin
  introversion: '#60a5fa', // endorphin
  openness: '#22d3ee',     // pulse
}

interface SelfResponse {
  traits: Record<string, number>
  genome_seed: string
  age_days: number
  life_stage: string
}

interface Props {
  traits: Record<string, number>
}

function TraitBar({ name, value }: { name: string; value: number }) {
  const color = TRAIT_COLORS[name] ?? '#64748b'
  const pct = Math.round(value * 100)

  return (
    <div className="flex items-center gap-3">
      <span className="text-xs font-mono text-text-dim w-24 capitalize shrink-0">{name}</span>
      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{
            width: `${Math.max(2, pct)}%`,
            backgroundColor: color,
          }}
        />
      </div>
      <span
        className="text-xs font-mono w-8 text-right shrink-0"
        style={{ color }}
      >
        {pct}%
      </span>
    </div>
  )
}

export function PersonalityTraits({ traits }: Props) {
  const traitOrder = ['curiosity', 'warmth', 'resilience', 'creativity', 'introversion', 'openness']

  const entries = traitOrder
    .filter(t => t in traits)
    .map(t => [t, traits[t]] as [string, number])

  // Append any unexpected traits not in the fixed order
  Object.entries(traits).forEach(([k, v]) => {
    if (!traitOrder.includes(k)) entries.push([k, v])
  })

  return (
    <div className="space-y-2">
      {entries.map(([name, value]) => (
        <TraitBar key={name} name={name} value={value} />
      ))}
    </div>
  )
}

export function PersonalityTraitsPanel() {
  const { data, isLoading } = useQuery<SelfResponse>({
    queryKey: ['self'],
    queryFn: () => fetch('/api/self').then(r => r.json()),
    refetchInterval: 10_000,
  })

  if (isLoading || !data) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3 animate-pulse">
            <div className="h-2.5 w-24 bg-muted rounded" />
            <div className="flex-1 h-1.5 bg-muted rounded-full" />
            <div className="h-2.5 w-8 bg-muted rounded" />
          </div>
        ))}
      </div>
    )
  }

  return <PersonalityTraits traits={data.traits} />
}
