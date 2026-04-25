import { useState } from 'react'
import { useSentiaStore } from '../stores/sentiaStore'
import { toggleLLM } from '../api/client'
import { clsx } from 'clsx'

export function LLMToggle() {
  const { state, setState } = useSentiaStore()
  const [loading, setLoading] = useState(false)
  const enabled = state?.llm_enabled ?? false

  const handleToggle = async () => {
    setLoading(true)
    try {
      await toggleLLM(!enabled)
      // State update will come via WebSocket
    } catch (e) {
      console.error('Toggle LLM failed', e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handleToggle}
      disabled={loading}
      className={clsx(
        'flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono transition-all',
        enabled
          ? 'bg-life/20 border border-life/40 text-life hover:bg-life/30'
          : 'bg-muted border border-subtle text-text-dim hover:bg-subtle',
        loading && 'opacity-50 cursor-wait'
      )}
    >
      <span
        className={clsx(
          'w-1.5 h-1.5 rounded-full',
          enabled ? 'bg-life animate-pulse' : 'bg-text-dim'
        )}
      />
      LLM {enabled ? 'ON' : 'OFF'}
    </button>
  )
}
