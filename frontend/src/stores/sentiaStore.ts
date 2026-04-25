import { create } from 'zustand'
import type { SentiaState, SentiaEvent, ModelInfo } from '../types/events'

interface ChatMessage {
  id: string
  role: 'human' | 'sentia'
  content: string
  timestamp: string
  emotion?: string
}

interface SentiaStore {
  // Connection
  connected: boolean
  wsError: string | null
  setConnected: (v: boolean) => void
  setWsError: (e: string | null) => void

  // Organism state
  state: SentiaState | null
  setState: (s: SentiaState) => void

  // Events feed
  events: SentiaEvent[]
  pushEvent: (e: SentiaEvent) => void
  clearEvents: () => void

  // Models
  models: ModelInfo[]
  modelsLoading: boolean
  ollamaRunning: boolean
  ollamaVersion: string
  setModels: (m: ModelInfo[], running: boolean, version: string) => void

  // Chat
  messages: ChatMessage[]
  addMessage: (m: ChatMessage) => void

  // UI
  llmThinking: boolean
  setLlmThinking: (v: boolean) => void
}

export const useSentiaStore = create<SentiaStore>((set) => ({
  connected: false,
  wsError: null,
  setConnected: (v) => set({ connected: v }),
  setWsError: (e) => set({ wsError: e }),

  state: null,
  setState: (s) => set({ state: s }),

  events: [],
  pushEvent: (e) =>
    set((prev) => ({
      events: [e, ...prev.events].slice(0, 200), // keep last 200
    })),
  clearEvents: () => set({ events: [] }),

  models: [],
  modelsLoading: false,
  ollamaRunning: false,
  ollamaVersion: '',
  setModels: (m, running, version) =>
    set({ models: m, ollamaRunning: running, ollamaVersion: version }),

  messages: [],
  addMessage: (m) =>
    set((prev) => ({ messages: [...prev.messages, m] })),

  llmThinking: false,
  setLlmThinking: (v) => set({ llmThinking: v }),
}))
