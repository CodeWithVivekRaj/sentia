import { useSentiaStore } from '../stores/sentiaStore'
import { NeedsBar } from '../components/NeedsBar'
import { ChemistryGauge } from '../components/ChemistryGauge'
import { EmotionDisplay } from '../components/EmotionDisplay'
import { EventFeed } from '../components/EventFeed'
import { ChatPanel } from '../components/ChatPanel'
import { formatDistanceToNow } from 'date-fns'
import { clsx } from 'clsx'

function Panel({ title, children, className }: {
  title: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={clsx('bg-panel border border-border rounded-xl p-4', className)}>
      <h3 className="text-xs font-mono text-text-dim uppercase tracking-wider mb-3">{title}</h3>
      {children}
    </div>
  )
}

export function LifeMonitor() {
  const { state } = useSentiaStore()

  if (!state) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-text-dim font-mono text-sm animate-pulse">
          Connecting to Sentia...
        </div>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-12 gap-4 h-full overflow-hidden">

      {/* Left column: Identity + Needs + Events */}
      <div className="col-span-3 flex flex-col gap-4 overflow-y-auto min-h-0">

        {/* Identity */}
        <Panel title="Identity">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className={clsx(
                'w-3 h-3 rounded-full animate-glow',
                state.is_alive ? 'bg-life' : 'bg-red-500'
              )} />
              <span className="text-lg font-mono font-bold text-text">Sentia</span>
            </div>
            <div className="space-y-1 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-text-dim">Stage</span>
                <span className="text-life capitalize">{state.life_stage}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-dim">Age</span>
                <span className="text-text-muted">{state.age_days.toFixed(1)} days</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-dim">Born</span>
                <span className="text-text-muted text-[10px]">
                  {state.born_at
                    ? formatDistanceToNow(new Date(state.born_at), { addSuffix: true })
                    : 'unknown'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-dim">Events</span>
                <span className="text-text-muted">{state.total_events.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </Panel>

        {/* Needs */}
        <Panel title="Needs">
          <NeedsBar needs={state.needs} />
        </Panel>

        {/* Event feed */}
        <Panel title="Event Stream" className="flex-1 overflow-hidden flex flex-col min-h-0">
          <div className="flex-1 overflow-y-auto min-h-0">
            <EventFeed />
          </div>
        </Panel>
      </div>

      {/* Middle column: Chemistry + Emotions */}
      <div className="col-span-3 flex flex-col gap-4 overflow-y-auto min-h-0">

        <Panel title="Neurochemistry">
          <ChemistryGauge chemistry={state.chemistry} />
        </Panel>

        <Panel title="Emotions">
          <EmotionDisplay
            emotions={state.emotions}
            dominant={state.dominant_emotion}
            mood={state.mood}
          />
        </Panel>

        {/* Last thought */}
        <Panel title="Last Thought">
          {state.last_thought ? (
            <div>
              <p className="text-sm text-text leading-relaxed italic">"{state.last_thought}"</p>
              {state.last_thought_at && (
                <p className="text-[10px] text-text-dim font-mono mt-2">
                  {formatDistanceToNow(new Date(state.last_thought_at), { addSuffix: true })}
                </p>
              )}
            </div>
          ) : (
            <p className="text-xs text-text-dim italic font-mono">No thoughts yet...</p>
          )}
        </Panel>
      </div>

      {/* Right column: Chat */}
      <div className="col-span-6 flex flex-col min-h-0">
        <Panel title="Conversation" className="flex-1 overflow-hidden flex flex-col min-h-0">
          <div className="flex-1 overflow-hidden flex flex-col min-h-0">
            <ChatPanel />
          </div>
        </Panel>
      </div>
    </div>
  )
}
