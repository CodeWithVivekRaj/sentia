import { clsx } from 'clsx'

const EMOTION_COLORS: Record<string, string> = {
  curious: '#c084fc',
  joy: '#34d399',
  fear: '#f97316',
  love: '#fb7185',
  boredom: '#64748b',
  calm: '#60a5fa',
  pain: '#ef4444',
  excitement: '#facc15',
  sadness: '#818cf8',
  anger: '#dc2626',
  wonder: '#06b6d4',
  contentment: '#10b981',
}

interface Props {
  emotions: Record<string, number>
  dominant: string
  mood: string
}

export function EmotionDisplay({ emotions, dominant, mood }: Props) {
  const sorted = Object.entries(emotions).sort(([, a], [, b]) => b - a).slice(0, 6)

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span
          className="text-2xl font-mono font-bold capitalize"
          style={{ color: EMOTION_COLORS[dominant] ?? '#a78bfa' }}
        >
          {dominant}
        </span>
        <span className="text-xs text-text-dim font-mono">· {mood}</span>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {sorted.map(([emotion, intensity]) => (
          <span
            key={emotion}
            className="px-2 py-0.5 rounded-full text-[10px] font-mono capitalize border"
            style={{
              color: EMOTION_COLORS[emotion] ?? '#94a3b8',
              borderColor: `${EMOTION_COLORS[emotion] ?? '#94a3b8'}40`,
              backgroundColor: `${EMOTION_COLORS[emotion] ?? '#94a3b8'}10`,
              opacity: 0.5 + intensity * 0.5,
            }}
          >
            {emotion} {Math.round(intensity * 100)}%
          </span>
        ))}
        {sorted.length === 0 && (
          <span className="text-xs text-text-dim font-mono italic">no strong emotions</span>
        )}
      </div>
    </div>
  )
}
