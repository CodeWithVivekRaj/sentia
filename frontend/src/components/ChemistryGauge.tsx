import { clsx } from 'clsx'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts'

const CHEM_COLORS: Record<string, string> = {
  dopamine: '#c084fc',
  serotonin: '#34d399',
  cortisol: '#f97316',
  oxytocin: '#fb7185',
  endorphins: '#60a5fa',
  adrenaline: '#facc15',
  melatonin: '#818cf8',
}

interface Props {
  chemistry: Record<string, number>
}

export function ChemistryGauge({ chemistry }: Props) {
  const data = Object.entries(chemistry).map(([name, value]) => ({
    subject: name.slice(0, 5),
    value: Math.round(value * 100),
    fullMark: 100,
  }))

  return (
    <div>
      <ResponsiveContainer width="100%" height={200}>
        <RadarChart data={data} margin={{ top: 0, right: 20, bottom: 0, left: 20 }}>
          <PolarGrid stroke="#1e1e2e" />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'monospace' }}
          />
          <Radar
            name="chemistry"
            dataKey="value"
            stroke="#a78bfa"
            fill="#a78bfa"
            fillOpacity={0.2}
          />
        </RadarChart>
      </ResponsiveContainer>
      <div className="grid grid-cols-2 gap-1.5 mt-2">
        {Object.entries(chemistry).map(([name, value]) => (
          <div key={name} className="flex items-center gap-1.5">
            <span
              className="w-1.5 h-1.5 rounded-full shrink-0"
              style={{ backgroundColor: CHEM_COLORS[name] ?? '#64748b' }}
            />
            <span className="text-[10px] font-mono text-text-dim capitalize truncate">{name}</span>
            <span
              className="text-[10px] font-mono ml-auto"
              style={{ color: CHEM_COLORS[name] ?? '#64748b' }}
            >
              {Math.round(value * 100)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
