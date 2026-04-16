import clsx from 'clsx'

const STATUS_STYLE = {
  applied:     'bg-accent-blue2 text-accent-blue border border-accent-blue/30',
  in_progress: 'bg-accent-amber2 text-accent-amber border border-accent-amber/30',
  queued:      'bg-bg-raised text-txt-muted border border-border-dim',
  failed:      'bg-accent-red2 text-accent-red border border-accent-red/30',
  skipped:     'bg-bg-raised text-txt-muted border border-border-dim',
}

const PORTAL_BADGE = {
  internshala: { label: 'IN', bg: 'bg-accent-green2 text-accent-green' },
  linkedin:    { label: 'LI', bg: 'bg-accent-blue2  text-accent-blue'  },
  naukri:      { label: 'NK', bg: 'bg-accent-amber2 text-accent-amber' },
}

export default function JobQueue({ applications = [] }) {
  if (applications.length === 0) {
    return (
      <p className="text-txt-muted text-sm py-3">No applications yet — run the agent to start applying.</p>
    )
  }

  return (
    <div className="flex flex-col gap-1.5">
      {applications.map((app) => {
        const badge = PORTAL_BADGE[app.portal] || { label: '??', bg: 'bg-bg-raised text-txt-muted' }
        return (
          <div
            key={app.id}
            className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-bg-raised border border-transparent hover:border-border-base transition-colors"
          >
            <div className={clsx('w-7 h-7 rounded-md flex items-center justify-center text-[10px] font-mono font-medium shrink-0', badge.bg)}>
              {badge.label}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[12px] text-txt-primary truncate">{app.job_title || 'Untitled role'}</p>
              <p className="text-[10px] font-mono text-txt-muted">{app.company} · {app.portal}</p>
            </div>
            {app.match_score > 0 && (
              <span className="text-[10px] font-mono text-txt-muted shrink-0">{Math.round(app.match_score)}%</span>
            )}
            <span className={clsx('text-[10px] font-mono px-2 py-0.5 rounded shrink-0', STATUS_STYLE[app.status])}>
              {app.status.replace('_', ' ')}
            </span>
          </div>
        )
      })}
    </div>
  )
}