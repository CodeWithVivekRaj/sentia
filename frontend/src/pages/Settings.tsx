import { useSentiaStore } from '../stores/sentiaStore'
import { listModels, selectModel, toggleLLM } from '../api/client'
import { useState } from 'react'
import { clsx } from 'clsx'

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-panel border border-border rounded-xl p-5">
      <h3 className="text-sm font-mono font-semibold text-text mb-4">{title}</h3>
      {children}
    </div>
  )
}

export function Settings() {
  const { state, models, ollamaRunning, ollamaVersion, setModels } = useSentiaStore()
  const [pulling, setPulling] = useState(false)
  const [pullModel, setPullModel] = useState('')
  const [pullLog, setPullLog] = useState<string[]>([])
  const [toggling, setToggling] = useState(false)

  const handlePull = async () => {
    if (!pullModel.trim()) return
    setPulling(true)
    setPullLog([])
    try {
      const resp = await fetch(`/api/models/pull`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: pullModel.trim() }),
      })
      const reader = resp.body?.getReader()
      const decoder = new TextDecoder()
      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const text = decoder.decode(value)
          const lines = text.split('\n').filter(l => l.startsWith('data: '))
          for (const line of lines) {
            try {
              const data = JSON.parse(line.slice(6))
              setPullLog(prev => [...prev.slice(-20), data.status ?? JSON.stringify(data)])
            } catch {}
          }
        }
      }
    } finally {
      setPulling(false)
      // Refresh model list
      const data = await listModels()
      setModels(data.models, data.ollama_running, data.ollama_version)
    }
  }

  const handleToggleLLM = async () => {
    setToggling(true)
    try {
      await toggleLLM(!state?.llm_enabled)
    } finally {
      setToggling(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <h2 className="text-lg font-mono font-bold text-text">Settings</h2>

      <Section title="LLM Control">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-text">Language Model</p>
            <p className="text-xs text-text-dim mt-0.5">
              When disabled, Sentia's body keeps running but mind is silent.
            </p>
          </div>
          <button
            onClick={handleToggleLLM}
            disabled={toggling}
            className={clsx(
              'px-4 py-2 rounded-lg text-xs font-mono transition-all border',
              state?.llm_enabled
                ? 'bg-life/20 border-life/40 text-life hover:bg-life/30'
                : 'bg-muted border-subtle text-text-dim hover:bg-subtle'
            )}
          >
            {toggling ? '...' : state?.llm_enabled ? 'ON' : 'OFF'}
          </button>
        </div>
        <div className="mt-3 text-xs text-text-dim font-mono">
          Current model: <span className="text-text">{state?.current_model}</span>
        </div>
      </Section>

      <Section title="Ollama Status">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className={clsx('w-2 h-2 rounded-full', ollamaRunning ? 'bg-serotonin' : 'bg-red-500')} />
            <span className="text-sm text-text">{ollamaRunning ? 'Running' : 'Not running'}</span>
            {ollamaVersion && <span className="text-xs text-text-dim">v{ollamaVersion}</span>}
          </div>
          {!ollamaRunning && (
            <p className="text-xs text-cortisol font-mono">
              Start Ollama: <code>ollama serve</code>
            </p>
          )}
        </div>
      </Section>

      <Section title="Install Model">
        <div className="space-y-3">
          <p className="text-xs text-text-dim">
            Pull a model from Ollama library. Models under ~4.5GB fit in 6GB VRAM.
          </p>
          <div className="flex gap-2">
            <input
              value={pullModel}
              onChange={e => setPullModel(e.target.value)}
              placeholder="e.g. llama3.2:3b"
              className="flex-1 bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text placeholder:text-text-dim outline-none focus:border-life/40 font-mono"
            />
            <button
              onClick={handlePull}
              disabled={pulling || !pullModel.trim()}
              className="px-4 py-2 bg-life/20 border border-life/40 text-life rounded-lg text-xs font-mono hover:bg-life/30 disabled:opacity-40"
            >
              {pulling ? 'Pulling...' : 'Pull'}
            </button>
          </div>
          {pullLog.length > 0 && (
            <div className="bg-surface border border-border rounded p-2 max-h-32 overflow-y-auto">
              {pullLog.map((line, i) => (
                <div key={i} className="text-[10px] font-mono text-text-dim">{line}</div>
              ))}
            </div>
          )}
        </div>
      </Section>

      <Section title="Installed Models">
        {models.length === 0 ? (
          <p className="text-xs text-text-dim font-mono">
            {ollamaRunning ? 'No models installed' : 'Ollama not running'}
          </p>
        ) : (
          <div className="space-y-1.5">
            {models.map(m => (
              <div key={m.name} className="flex items-center justify-between py-1.5 border-b border-border last:border-0">
                <div>
                  <span className="text-sm font-mono text-text">{m.name}</span>
                  {m.name === state?.current_model && (
                    <span className="ml-2 text-[10px] text-life">active</span>
                  )}
                </div>
                <div className="flex items-center gap-3 text-xs font-mono text-text-dim">
                  <span>{m.size_gb} GB</span>
                  <span className={clsx(m.fits_in_vram ? 'text-serotonin' : 'text-cortisol')}>
                    ~{m.vram_estimate_gb} GB VRAM
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>
    </div>
  )
}
