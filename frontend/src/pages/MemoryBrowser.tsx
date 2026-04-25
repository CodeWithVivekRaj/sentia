import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'

interface MemoryRecord {
  id: string
  content: string
  source_event_type: string
  emotion: string
  emotion_intensity: number
  mood: string
  needs_snapshot: Record<string, number>
  formed_at: string
  salience: number
  strength: number
  last_recalled_at: string | null
  recall_count: number
  similarity?: number
}

interface MemoryListResponse {
  memories: MemoryRecord[]
  total: number
}

interface RecallResponse {
  query: string
  memories: MemoryRecord[]
}

const EMOTION_COLORS: Record<string, string> = {
  wonder: 'text-pulse',
  joy: 'text-serotonin',
  calm: 'text-endorphin',
  contentment: 'text-serotonin',
  love: 'text-oxytocin',
  hope: 'text-dopamine',
  anxiety: 'text-cortisol',
  fear: 'text-cortisol',
  sadness: 'text-melatonin',
  loneliness: 'text-melatonin',
  anger: 'text-adrenaline',
  frustration: 'text-adrenaline',
  curiosity: 'text-dopamine',
}

function emotionColor(emotion: string): string {
  return EMOTION_COLORS[emotion] ?? 'text-text-muted'
}

function strengthBar(strength: number) {
  const pct = Math.round(strength * 100)
  const color =
    strength > 0.6 ? 'bg-serotonin' : strength > 0.3 ? 'bg-adrenaline' : 'bg-cortisol'
  return (
    <div className="flex items-center gap-1.5">
      <div className="h-1 w-16 bg-muted rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-text-dim text-xs font-mono">{pct}%</span>
    </div>
  )
}

function MemoryCard({ memory }: { memory: MemoryRecord }) {
  const date = new Date(memory.formed_at)
  const timeStr = date.toLocaleString(undefined, {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
  const opacity = Math.max(0.25, memory.strength)

  return (
    <div
      className="border border-border rounded-lg p-3 bg-panel hover:border-subtle transition-colors"
      style={{ opacity }}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <p className="text-text text-sm leading-snug flex-1">{memory.content}</p>
        <span className="shrink-0 text-xs font-mono text-text-dim">{timeStr}</span>
      </div>
      <div className="flex items-center gap-3 flex-wrap">
        <span className={`text-xs font-mono font-semibold ${emotionColor(memory.emotion)}`}>
          {memory.emotion}
        </span>
        <span className="text-text-dim text-xs font-mono">{memory.mood}</span>
        <span className="text-text-dim text-xs font-mono">
          salience {Math.round(memory.salience * 100)}%
        </span>
        {strengthBar(memory.strength)}
        {memory.recall_count > 0 && (
          <span className="text-pulse text-xs font-mono">recalled {memory.recall_count}×</span>
        )}
        {memory.similarity !== undefined && (
          <span className="text-life text-xs font-mono">
            sim {(memory.similarity * 100).toFixed(0)}%
          </span>
        )}
        <span className="text-text-dim text-xs font-mono ml-auto opacity-50 text-right truncate max-w-[120px]">
          {memory.source_event_type}
        </span>
      </div>
    </div>
  )
}

function MemoryStats() {
  const { data } = useQuery<{ total: number; embedding_dim: number | null }>({
    queryKey: ['memory-stats'],
    queryFn: () => fetch('/api/memories/stats').then(r => r.json()),
    refetchInterval: 5000,
  })
  if (!data) return null
  return (
    <div className="flex items-center gap-4 text-xs font-mono text-text-dim">
      <span>{data.total} memories</span>
      {data.embedding_dim && <span>{data.embedding_dim}-dim embeddings</span>}
    </div>
  )
}

export function MemoryBrowser() {
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [page, setPage] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const PAGE_SIZE = 30

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query.trim()), 400)
    return () => clearTimeout(t)
  }, [query])

  const { data: listData, isLoading: listLoading } = useQuery<MemoryListResponse>({
    queryKey: ['memories', page],
    queryFn: () =>
      fetch(`/api/memories?limit=${PAGE_SIZE}&offset=${page * PAGE_SIZE}`).then(r => r.json()),
    enabled: !debouncedQuery,
    refetchInterval: 5000,
  })

  const { data: recallData, isLoading: recallLoading } = useQuery<RecallResponse>({
    queryKey: ['memories-recall', debouncedQuery],
    queryFn: () =>
      fetch(`/api/memories/recall?q=${encodeURIComponent(debouncedQuery)}&k=20`).then(r => r.json()),
    enabled: !!debouncedQuery,
  })

  const memories = debouncedQuery
    ? (recallData?.memories ?? [])
    : (listData?.memories ?? [])
  const total = debouncedQuery ? memories.length : (listData?.total ?? 0)
  const isLoading = debouncedQuery ? recallLoading : listLoading
  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="h-full flex flex-col min-h-0 gap-3">
      {/* Header */}
      <div className="shrink-0 flex items-center justify-between">
        <div>
          <h1 className="text-text font-mono font-semibold text-sm">Memory Browser</h1>
          <MemoryStats />
        </div>
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => { setQuery(e.target.value); setPage(0) }}
            placeholder="Search memories..."
            className="bg-panel border border-border rounded px-2.5 py-1.5 text-xs font-mono text-text placeholder-text-dim focus:outline-none focus:border-life/40 w-56"
          />
          {query && (
            <button
              onClick={() => { setQuery(''); setPage(0) }}
              className="text-text-dim hover:text-text text-xs font-mono px-1.5 py-1 rounded border border-border"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Memory list */}
      <div className="flex-1 overflow-y-auto min-h-0 space-y-2 pr-1">
        {isLoading && memories.length === 0 && (
          <div className="flex items-center justify-center h-32">
            <span className="text-text-dim text-xs font-mono animate-pulse">loading memories…</span>
          </div>
        )}

        {!isLoading && memories.length === 0 && (
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <p className="text-text-dim text-xs font-mono">
                {debouncedQuery ? 'No memories match that query.' : 'No memories yet.'}
              </p>
              {!debouncedQuery && (
                <p className="text-text-dim text-xs font-mono opacity-50 mt-1">
                  Sentia forms memories as she experiences events.
                </p>
              )}
            </div>
          </div>
        )}

        {memories.map(m => (
          <MemoryCard key={m.id} memory={m} />
        ))}
      </div>

      {/* Pagination (browse mode only) */}
      {!debouncedQuery && totalPages > 1 && (
        <div className="shrink-0 flex items-center justify-between text-xs font-mono text-text-dim border-t border-border pt-2">
          <span>{total} total</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-2 py-0.5 rounded border border-border disabled:opacity-30 hover:border-subtle"
            >
              ← prev
            </button>
            <span>{page + 1} / {totalPages}</span>
            <button
              onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="px-2 py-0.5 rounded border border-border disabled:opacity-30 hover:border-subtle"
            >
              next →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
