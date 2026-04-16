export default function MetricCards({ stats }) {
  const cards = [
    {
      label: 'Applied today',
      value: stats?.total_today ?? '—',
      sub: stats ? `+${stats.total_today} since yesterday` : 'loading…',
      color: 'text-accent-green',
    },
    {
      label: 'Total applied',
      value: stats?.total_applied ?? '—',
      sub: 'across all portals',
      color: 'text-accent-blue',
    },
    {
      label: 'Interviews',
      value: stats?.interview_calls ?? '—',
      sub: stats?.total_applied
        ? `${((stats.interview_calls / stats.total_applied) * 100).toFixed(1)}% hit rate`
        : '—',
      color: 'text-accent-amber',
    },
    {
      label: 'Hours saved',
      value: stats?.hours_saved ?? '—',
      sub: 'est. @30 min/app',
      color: 'text-accent-green',
    },
  ]

  return (
    <div className="grid grid-cols-4 gap-2.5">
      {cards.map((c) => (
        <div key={c.label} className="bg-bg-surface border border-border-dim rounded-xl p-3.5">
          <p className="text-[10px] font-mono text-txt-muted uppercase tracking-wider mb-1.5">{c.label}</p>
          <p className={`text-2xl font-light ${c.color} leading-none`}>{c.value}</p>
          <p className="text-[10px] font-mono text-txt-muted mt-1">{c.sub}</p>
        </div>
      ))}
    </div>
  )
}