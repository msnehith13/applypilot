import { useEffect, useRef } from 'react'
import clsx from 'clsx'

const LEVEL_STYLE = {
  success: 'text-accent-green',
  info:    'text-txt-secondary',
  warning: 'text-accent-amber',
  error:   'text-accent-red',
}

const LEVEL_PREFIX = {
  success: '✓',
  info:    '→',
  warning: '⚠',
  error:   '✗',
}

function fmtTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toTimeString().slice(0, 8)
}

export default function AgentLogFeed({ logs, maxHeight = 200 }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs.length])

  return (
    <div
      className="overflow-y-auto font-mono text-[11px] leading-relaxed"
      style={{ maxHeight }}
    >
      {logs.length === 0 && (
        <p className="text-txt-muted py-2">No logs yet — start a run to see live output.</p>
      )}
      {logs.map((log, i) => (
        <div key={i} className="log-line flex gap-2 py-0.5">
          <span className="text-txt-muted shrink-0 w-16">{fmtTime(log.timestamp)}</span>
          <span className={clsx('shrink-0', LEVEL_STYLE[log.level] || 'text-txt-secondary')}>
            {LEVEL_PREFIX[log.level] || '·'}
          </span>
          <span className={clsx(LEVEL_STYLE[log.level] || 'text-txt-secondary')}>
            {log.message}
          </span>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}