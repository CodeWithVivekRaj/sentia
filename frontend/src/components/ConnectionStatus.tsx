import { useSentiaStore } from '../stores/sentiaStore'
import { clsx } from 'clsx'

export function ConnectionStatus() {
  const { connected, wsError, state } = useSentiaStore()

  return (
    <div className="flex items-center gap-2">
      <span
        className={clsx(
          'inline-block w-2 h-2 rounded-full',
          connected ? 'bg-serotonin animate-pulse' : 'bg-red-500'
        )}
      />
      <span className="text-xs text-text-muted font-mono">
        {connected ? 'connected' : wsError ?? 'disconnected'}
      </span>
      {state?.is_alive && (
        <span className="text-xs text-life font-mono ml-2 animate-breathe">
          ● alive
        </span>
      )}
    </div>
  )
}
