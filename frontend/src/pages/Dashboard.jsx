import { useState, useEffect } from 'react'
import { api } from '../api'
import { useStats } from '../hooks/useStats'
import MetricCards from '../components/MetricCards'
import AgentLogFeed from '../components/AgentLogFeed'
import JobQueue from '../components/JobQueue'
import clsx from 'clsx'

const PORTALS = [
  { id: 'internshala', label: 'Internshala' },
  { id: 'linkedin',    label: 'LinkedIn'    },
  { id: 'naukri',      label: 'Naukri'      },
]

const PIPELINE_STEPS = [
  { label: 'Login & session init',     key: 0 },
  { label: 'Filter & rank jobs',       key: 1 },
  { label: 'Fill forms + upload resume', key: 2 },
  { label: 'Generate cover letters',   key: 3 },
  { label: 'Log & notify results',     key: 4 },
]

function getPipelineStatus(logs, stepIndex) {
  // Infer pipeline progress from log messages
  const msgs = logs.map(l => l.message?.toLowerCase() || '')
  if (stepIndex === 0 && msgs.some(m => m.includes('logged in') || m.includes('session'))) return 'done'
  if (stepIndex === 1 && msgs.some(m => m.includes('found') || m.includes('filter'))) return 'done'
  if (stepIndex === 2 && msgs.some(m => m.includes('filling') || m.includes('uploading'))) return 'running'
  if (stepIndex === 2 && msgs.some(m => m.includes('applied'))) return 'done'
  if (stepIndex === 3 && msgs.some(m => m.includes('cover letter'))) return 'running'
  if (stepIndex === 4 && msgs.some(m => m.includes('complete'))) return 'done'
  return 'queued'
}

const STEP_STYLE = {
  done:    'bg-accent-green2 text-accent-green border-accent-green3',
  running: 'bg-accent-amber2 text-accent-amber border-accent-amber/30',
  queued:  'bg-bg-raised text-txt-muted border-border-dim',
}

export default function Dashboard({ logs, isRunning, activeRunId, clearLogs }) {
  const { stats } = useStats()
  const [selectedPortals, setSelectedPortals] = useState(['internshala'])
  const [recentApps, setRecentApps] = useState([])
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState('')

  // Load recent applications
  useEffect(() => {
    api.listApps({ limit: 8 }).then(setRecentApps).catch(() => {})
    const id = setInterval(() => {
      api.listApps({ limit: 8 }).then(setRecentApps).catch(() => {})
    }, 8000)
    return () => clearInterval(id)
  }, [])

  function togglePortal(id) {
    setSelectedPortals(prev =>
      prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
    )
  }

  async function handleStartRun() {
    if (selectedPortals.length === 0) { setError('Select at least one portal'); return }
    setError('')
    setStarting(true)
    clearLogs()
    try {
      await api.startRun(selectedPortals)
    } catch (e) {
      setError(e.message)
    } finally {
      setStarting(false)
    }
  }

  async function handleStopRun() {
    if (!activeRunId) return
    try { await api.stopRun(activeRunId) } catch {}
  }

  // Progress from log count
  const doneSteps = PIPELINE_STEPS.filter((_, i) => getPipelineStatus(logs, i) === 'done').length
  const pct = Math.round((doneSteps / PIPELINE_STEPS.length) * 100)

  return (
    <div className="p-6 flex flex-col gap-5">

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-light text-txt-primary tracking-tight">Dashboard</h1>
          <p className="text-[11px] font-mono text-txt-muted mt-0.5">
            {new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'short', year: 'numeric' })}
          </p>
        </div>

        {/* Run controls */}
        <div className="flex items-center gap-2">
          {/* Portal toggles */}
          <div className="flex gap-1.5 mr-2">
            {PORTALS.map(p => (
              <button
                key={p.id}
                onClick={() => togglePortal(p.id)}
                disabled={isRunning}
                className={clsx(
                  'px-3 py-1.5 rounded-lg text-[11px] font-mono border transition-colors disabled:opacity-40',
                  selectedPortals.includes(p.id)
                    ? 'bg-accent-green2 text-accent-green border-accent-green3'
                    : 'bg-bg-raised text-txt-muted border-border-dim hover:border-border-base'
                )}
              >
                {p.label}
              </button>
            ))}
          </div>

          {isRunning ? (
            <button
              onClick={handleStopRun}
              className="flex items-center gap-2 px-4 py-2 bg-accent-red2 border border-accent-red/30 text-accent-red rounded-lg text-sm font-medium hover:opacity-80 transition-opacity"
            >
              <span className="w-2 h-2 rounded-sm bg-accent-red" />
              Stop
            </button>
          ) : (
            <button
              onClick={handleStartRun}
              disabled={starting}
              className="flex items-center gap-2 px-4 py-2 bg-accent-green text-bg-base rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              <PlayIcon />
              {starting ? 'Starting…' : 'Run Agent'}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-accent-red2 border border-accent-red/30 text-accent-red text-sm px-4 py-2 rounded-lg font-mono">
          {error}
        </div>
      )}

      {/* Metrics */}
      <MetricCards stats={stats} />

      {/* Middle row: pipeline + recent jobs */}
      <div className="grid grid-cols-2 gap-4">

        {/* Pipeline */}
        <div className="bg-bg-surface border border-border-dim rounded-xl p-4">
          <p className="text-[10px] font-mono text-txt-muted uppercase tracking-wider mb-3">Agent pipeline</p>
          <div className="flex flex-col gap-2">
            {PIPELINE_STEPS.map((step, i) => {
              const st = isRunning ? getPipelineStatus(logs, i) : 'queued'
              return (
                <div key={i} className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-bg-raised">
                  <div className="w-5 h-5 rounded flex items-center justify-center shrink-0">
                    {st === 'done'    && <CheckIcon />}
                    {st === 'running' && <SpinIcon />}
                    {st === 'queued'  && <DotIcon />}
                  </div>
                  <span className="text-[12px] text-txt-secondary flex-1">{step.label}</span>
                  <span className={clsx('text-[10px] font-mono px-2 py-0.5 rounded border', STEP_STYLE[st])}>
                    {st}
                  </span>
                </div>
              )
            })}
          </div>
          {/* Progress bar */}
          <div className="mt-3 h-0.5 bg-border-dim rounded-full overflow-hidden">
            <div
              className="h-full bg-accent-green rounded-full transition-all duration-500"
              style={{ width: `${isRunning ? pct : 0}%` }}
            />
          </div>
          <p className="text-[10px] font-mono text-txt-muted mt-1.5">
            {isRunning ? `${doneSteps} / ${PIPELINE_STEPS.length} steps · ${pct}%` : 'Idle'}
          </p>
        </div>

        {/* Recent applications */}
        <div className="bg-bg-surface border border-border-dim rounded-xl p-4">
          <p className="text-[10px] font-mono text-txt-muted uppercase tracking-wider mb-3">Recent applications</p>
          <JobQueue applications={recentApps} />
        </div>
      </div>

      {/* Live log */}
      <div className="bg-bg-surface border border-border-dim rounded-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <p className="text-[10px] font-mono text-txt-muted uppercase tracking-wider">Agent log · live</p>
          {logs.length > 0 && (
            <button onClick={clearLogs} className="text-[10px] font-mono text-txt-muted hover:text-txt-secondary transition-colors">
              clear
            </button>
          )}
        </div>
        <AgentLogFeed logs={logs} maxHeight={180} />
      </div>

    </div>
  )
}

function PlayIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <path d="M2.5 2L9.5 6L2.5 10V2Z" fill="currentColor"/>
    </svg>
  )
}
function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="#4ade80" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 6L5 9L10 3"/>
    </svg>
  )
}
function SpinIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="#fbbf24" strokeWidth="1.8" strokeLinecap="round" style={{ animation: 'spin 1s linear infinite' }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <path d="M6 1v2M6 9v2M1 6h2M9 6h2" opacity="0.4"/>
      <path d="M2.5 2.5l1.4 1.4"/>
    </svg>
  )
}
function DotIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <circle cx="6" cy="6" r="2" fill="#6b7280"/>
    </svg>
  )
}