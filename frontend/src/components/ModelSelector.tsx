import { useEffect, useState } from 'react'
import { useSentiaStore } from '../stores/sentiaStore'
import { listModels, selectModel } from '../api/client'
import { clsx } from 'clsx'

export function ModelSelector() {
  const { models, ollamaRunning, ollamaVersion, setModels, state } = useSentiaStore()
  const [loading, setLoading] = useState(false)
  const [selecting, setSelecting] = useState(false)
  const [open, setOpen] = useState(false)

  const fetchModels = async () => {
    setLoading(true)
    try {
      const data = await listModels()
      setModels(data.models, data.ollama_running, data.ollama_version)
    } catch {
      setModels([], false, '')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchModels()
    const interval = setInterval(fetchModels, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleSelect = async (name: string) => {
    setSelecting(true)
    setOpen(false)
    try {
      await selectModel(name)
    } catch (e) {
      console.error('Model select failed', e)
    } finally {
      setSelecting(false)
    }
  }

  const currentModel = state?.current_model ?? 'none'

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        disabled={!ollamaRunning || selecting}
        className={clsx(
          'flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono transition-all',
          'bg-panel border border-border hover:border-subtle text-text-muted hover:text-text',
          (!ollamaRunning || selecting) && 'opacity-50 cursor-not-allowed'
        )}
      >
        <span className={clsx('w-1.5 h-1.5 rounded-full', ollamaRunning ? 'bg-serotonin' : 'bg-red-500')} />
        <span className="max-w-[160px] truncate">{selecting ? 'switching...' : currentModel}</span>
        <span className="text-text-dim">▾</span>
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-72 bg-panel border border-border rounded-lg shadow-xl z-50 overflow-hidden">
          <div className="px-3 py-2 border-b border-border flex items-center justify-between">
            <span className="text-xs text-text-muted font-mono">Installed models</span>
            <button onClick={fetchModels} className="text-xs text-text-dim hover:text-text">↻</button>
          </div>
          <div className="max-h-64 overflow-y-auto">
            {loading && (
              <div className="px-3 py-3 text-xs text-text-dim font-mono">Loading...</div>
            )}
            {!loading && models.length === 0 && (
              <div className="px-3 py-3 text-xs text-text-dim font-mono">
                {ollamaRunning ? 'No models installed' : 'Ollama not running'}
              </div>
            )}
            {models.map((m) => (
              <button
                key={m.name}
                onClick={() => handleSelect(m.name)}
                className={clsx(
                  'w-full flex items-center justify-between px-3 py-2.5 text-xs font-mono',
                  'hover:bg-muted transition-colors text-left',
                  m.name === currentModel && 'bg-life/10 text-life',
                  !m.fits_in_vram && 'opacity-60'
                )}
              >
                <span className="truncate">{m.name}</span>
                <div className="flex items-center gap-2 ml-2 shrink-0">
                  <span className="text-text-dim">{m.vram_estimate_gb}GB</span>
                  {!m.fits_in_vram && (
                    <span className="text-cortisol text-[10px]">⚠</span>
                  )}
                  {m.name === currentModel && (
                    <span className="text-life text-[10px]">✓</span>
                  )}
                </div>
              </button>
            ))}
          </div>
          <div className="px-3 py-1.5 border-t border-border">
            <span className="text-[10px] text-text-dim font-mono">
              Ollama {ollamaVersion} · 6GB VRAM
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
