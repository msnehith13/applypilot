import { useState, useEffect } from 'react'
import { api } from '../api'
import clsx from 'clsx'

const STATUS_OPTS = ['all', 'applied', 'in_progress', 'queued', 'failed', 'skipped']
const PORTAL_OPTS = ['all', 'internshala', 'linkedin', 'naukri']

const STATUS_STYLE = {
  applied:     'bg-accent-blue2 text-accent-blue',
  in_progress: 'bg-accent-amber2 text-accent-amber',
  queued:      'bg-bg-raised text-txt-muted',
  failed:      'bg-accent-red2 text-accent-red',
  skipped:     'bg-bg-raised text-txt-muted',
}

const PORTAL_COLOR = {
  internshala: 'text-accent-green',
  linkedin:    'text-accent-blue',
  naukri:      'text-accent-amber',
}

function fmtDate(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export default function Applications() {
  const [apps, setApps] = useState([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('all')
  const [portalFilter, setPortalFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    const params = {}
    if (statusFilter !== 'all') params.status = statusFilter
    if (portalFilter !== 'all') params.portal = portalFilter
    params.limit = 200
    api.listApps(params)
      .then(data => { setApps(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [statusFilter, portalFilter])

  const filtered = apps.filter(a => {
    if (!search) return true
    const q = search.toLowerCase()
    return (
      a.job_title?.toLowerCase().includes(q) ||
      a.company?.toLowerCase().includes(q)
    )
  })

  return (
    <div className="p-6 flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-light text-txt-primary tracking-tight">Applications</h1>
          <p className="text-[11px] font-mono text-txt-muted mt-0.5">{filtered.length} records</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <input
          type="text"
          placeholder="Search role or company…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="flex-1 max-w-xs bg-bg-surface border border-border-dim rounded-lg px-3 py-1.5 text-sm text-txt-primary placeholder-txt-muted focus:outline-none focus:border-border-strong"
        />

        <div className="flex gap-1">
          {STATUS_OPTS.map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={clsx(
                'px-3 py-1.5 rounded-lg text-[11px] font-mono border transition-colors',
                statusFilter === s
                  ? 'bg-bg-raised text-txt-primary border-border-base'
                  : 'text-txt-muted border-border-dim hover:border-border-base'
              )}
            >
              {s}
            </button>
          ))}
        </div>

        <div className="flex gap-1 ml-2">
          {PORTAL_OPTS.map(p => (
            <button
              key={p}
              onClick={() => setPortalFilter(p)}
              className={clsx(
                'px-3 py-1.5 rounded-lg text-[11px] font-mono border transition-colors',
                portalFilter === p
                  ? 'bg-bg-raised text-txt-primary border-border-base'
                  : 'text-txt-muted border-border-dim hover:border-border-base'
              )}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="bg-bg-surface border border-border-dim rounded-xl overflow-hidden">
        {loading ? (
          <p className="text-txt-muted text-sm p-6 font-mono">Loading…</p>
        ) : filtered.length === 0 ? (
          <p className="text-txt-muted text-sm p-6 font-mono">No applications match these filters.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-dim">
                {['Role', 'Company', 'Portal', 'Match', 'Status', 'Applied at'].map(h => (
                  <th key={h} className="text-left text-[10px] font-mono text-txt-muted uppercase tracking-wider px-4 py-3">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((app, i) => (
                <tr
                  key={app.id}
                  onClick={() => setSelected(selected?.id === app.id ? null : app)}
                  className={clsx(
                    'border-b border-border-dim cursor-pointer transition-colors',
                    i % 2 === 0 ? 'bg-bg-base' : 'bg-bg-surface',
                    'hover:bg-bg-raised',
                    selected?.id === app.id && 'bg-bg-raised'
                  )}
                >
                  <td className="px-4 py-3 text-txt-primary text-[12px] max-w-[200px] truncate">{app.job_title || '—'}</td>
                  <td className="px-4 py-3 text-txt-secondary text-[12px]">{app.company || '—'}</td>
                  <td className={clsx('px-4 py-3 text-[11px] font-mono', PORTAL_COLOR[app.portal] || 'text-txt-muted')}>
                    {app.portal}
                  </td>
                  <td className="px-4 py-3 text-[11px] font-mono text-txt-muted">
                    {app.match_score > 0 ? `${Math.round(app.match_score)}%` : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={clsx('text-[10px] font-mono px-2 py-0.5 rounded', STATUS_STYLE[app.status])}>
                      {app.status?.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-[11px] font-mono text-txt-muted">{fmtDate(app.applied_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Detail drawer */}
      {selected && (
        <div className="bg-bg-surface border border-border-dim rounded-xl p-5 flex flex-col gap-3">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-base font-medium text-txt-primary">{selected.job_title}</h2>
              <p className="text-[11px] font-mono text-txt-muted mt-0.5">{selected.company} · {selected.portal}</p>
            </div>
            <button onClick={() => setSelected(null)} className="text-txt-muted hover:text-txt-secondary text-lg leading-none">×</button>
          </div>

          {selected.job_url && (
            <a href={selected.job_url} target="_blank" rel="noreferrer"
               className="text-[11px] font-mono text-accent-blue hover:underline break-all">
              {selected.job_url}
            </a>
          )}

          {selected.cover_letter && (
            <div>
              <p className="text-[10px] font-mono text-txt-muted uppercase tracking-wider mb-2">Cover letter</p>
              <p className="text-[12px] text-txt-secondary leading-relaxed whitespace-pre-wrap bg-bg-raised rounded-lg p-3">
                {selected.cover_letter}
              </p>
            </div>
          )}

          {selected.job_description && (
            <div>
              <p className="text-[10px] font-mono text-txt-muted uppercase tracking-wider mb-2">Job description</p>
              <p className="text-[12px] text-txt-secondary leading-relaxed whitespace-pre-wrap bg-bg-raised rounded-lg p-3 max-h-48 overflow-y-auto">
                {selected.job_description}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}