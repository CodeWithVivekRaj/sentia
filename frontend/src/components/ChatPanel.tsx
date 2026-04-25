import { useState, useRef, useEffect } from 'react'
import { useSentiaStore } from '../stores/sentiaStore'
import { sendChat } from '../api/client'
import { clsx } from 'clsx'
import { formatDistanceToNow } from 'date-fns'

function genId() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36)
}

export function ChatPanel() {
  const { messages, addMessage, state, llmThinking, setLlmThinking } = useSentiaStore()
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    const content = input.trim()
    if (!content || llmThinking) return

    setInput('')
    addMessage({
      id: genId(),
      role: 'human',
      content,
      timestamp: new Date().toISOString(),
    })

    setLlmThinking(true)
    try {
      const resp = await sendChat(content)
      addMessage({
        id: genId(),
        role: 'sentia',
        content: resp.response,
        timestamp: new Date().toISOString(),
        emotion: resp.emotion,
      })
    } catch (e) {
      addMessage({
        id: genId(),
        role: 'sentia',
        content: '[connection lost]',
        timestamp: new Date().toISOString(),
      })
    } finally {
      setLlmThinking(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const llmEnabled = state?.llm_enabled ?? false

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto min-h-0 space-y-3 pb-2 pr-1">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <p className="text-text-dim text-xs font-mono italic">
              {llmEnabled
                ? `Sentia is ${state?.dominant_emotion ?? 'calm'}. Say something.`
                : 'LLM is offline. Enable it to talk with Sentia.'}
            </p>
          </div>
        )}
        {messages.map((m) => (
          <div
            key={m.id}
            className={clsx(
              'flex',
              m.role === 'human' ? 'justify-end' : 'justify-start'
            )}
          >
            <div
              className={clsx(
                'max-w-[80%] rounded-lg px-3 py-2 text-sm',
                m.role === 'human'
                  ? 'bg-muted text-text'
                  : m.initiated
                  ? 'bg-pulse/10 border border-pulse/30 text-text'
                  : 'bg-life/10 border border-life/20 text-text'
              )}
            >
              {m.role === 'sentia' && (
                <div className="text-[10px] font-mono mb-1 capitalize flex items-center gap-1.5">
                  {m.initiated && (
                    <span className="text-pulse/70">↗ reached out</span>
                  )}
                  {m.emotion && (
                    <span className={m.initiated ? 'text-pulse/50' : 'text-life/60'}>{m.emotion}</span>
                  )}
                </div>
              )}
              <p className="leading-relaxed whitespace-pre-wrap">{m.content}</p>
              <div className="text-[10px] text-text-dim mt-1 text-right">
                {formatDistanceToNow(new Date(m.timestamp), { addSuffix: true })}
              </div>
            </div>
          </div>
        ))}
        {llmThinking && (
          <div className="flex justify-start">
            <div className="bg-life/10 border border-life/20 rounded-lg px-3 py-2">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-life rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-life rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-life rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-border pt-3">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={llmEnabled ? 'Talk to Sentia...' : 'LLM offline'}
            disabled={!llmEnabled && messages.length === 0}
            rows={2}
            className={clsx(
              'flex-1 bg-panel border border-border rounded-lg px-3 py-2 text-sm text-text',
              'placeholder:text-text-dim resize-none outline-none',
              'focus:border-life/40 transition-colors font-mono'
            )}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || llmThinking}
            className={clsx(
              'px-4 rounded-lg text-xs font-mono transition-all self-end pb-2',
              'bg-life/20 border border-life/40 text-life hover:bg-life/30',
              'disabled:opacity-40 disabled:cursor-not-allowed'
            )}
          >
            send
          </button>
        </div>
        <p className="text-[10px] text-text-dim font-mono mt-1">Enter to send · Shift+Enter for newline</p>
      </div>
    </div>
  )
}
