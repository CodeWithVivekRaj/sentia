import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useWebSocket } from './hooks/useWebSocket'
import { ConnectionStatus } from './components/ConnectionStatus'
import { LLMToggle } from './components/LLMToggle'
import { ModelSelector } from './components/ModelSelector'
import { LifeMonitor } from './pages/LifeMonitor'
import { Settings } from './pages/Settings'
import { clsx } from 'clsx'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
})

const NAV_ITEMS = [
  { path: '/', label: 'Life Monitor' },
  { path: '/memory', label: 'Memory' },
  { path: '/genome', label: 'Genome' },
  { path: '/dreams', label: 'Dreams' },
  { path: '/chronicle', label: 'Chronicle' },
  { path: '/rewards', label: 'Rewards' },
  { path: '/settings', label: 'Settings' },
]

function AppShell() {
  useWebSocket()

  return (
    <div className="h-screen flex flex-col bg-void text-text overflow-hidden">
      {/* Top bar */}
      <header className="shrink-0 flex items-center justify-between px-4 py-2 border-b border-border bg-deep">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="text-life font-mono font-bold text-sm tracking-widest animate-breathe">
              SENTIA
            </span>
          </div>
          <nav className="flex items-center gap-1">
            {NAV_ITEMS.map(({ path, label }) => (
              <NavLink
                key={path}
                to={path}
                end={path === '/'}
                className={({ isActive }) =>
                  clsx(
                    'px-2.5 py-1 rounded text-xs font-mono transition-colors',
                    isActive
                      ? 'bg-life/10 text-life border border-life/20'
                      : 'text-text-dim hover:text-text hover:bg-panel'
                  )
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <ConnectionStatus />
          <LLMToggle />
          <ModelSelector />
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-hidden p-4">
        <Routes>
          <Route path="/" element={<LifeMonitor />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/memory" element={<Placeholder title="Memory Browser" phase={3} />} />
          <Route path="/genome" element={<Placeholder title="Genome Inspector" phase={10} />} />
          <Route path="/dreams" element={<Placeholder title="Dream Log" phase={7} />} />
          <Route path="/chronicle" element={<Placeholder title="Life Chronicle" phase={11} />} />
          <Route path="/rewards" element={<Placeholder title="Reward Editor" phase={6} />} />
        </Routes>
      </main>
    </div>
  )
}

function Placeholder({ title, phase }: { title: string; phase: number }) {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center space-y-2">
        <p className="text-text font-mono font-semibold">{title}</p>
        <p className="text-text-dim text-xs font-mono">Coming in Phase {phase}</p>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppShell />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
