import { NavLink } from 'react-router-dom'
import clsx from 'clsx'

const NAV = [
  { to: '/',             label: 'Dashboard',    icon: GridIcon },
  { to: '/applications', label: 'Applications', icon: ListIcon },
  { to: '/profile',      label: 'Profile',      icon: UserIcon },
  { to: '/settings',     label: 'Settings',     icon: GearIcon },
]

export default function Sidebar({ isRunning }) {
  return (
    <aside className="w-52 shrink-0 bg-bg-surface border-r border-border-dim flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 py-4 border-b border-border-dim">
        <div className="w-7 h-7 bg-accent-green rounded-lg flex items-center justify-center shrink-0">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2 7L5.5 10.5L12 4" stroke="#0a0b0d" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <span className="font-sans text-[17px] text-txt-primary tracking-tight">
          Apply<span className="text-accent-green">Pilot</span>
        </span>
      </div>

      {/* Agent status */}
      <div className="px-4 py-3 border-b border-border-dim">
        <div className={clsx(
          'flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-mono',
          isRunning
            ? 'bg-accent-green2 border border-accent-green3 text-accent-green'
            : 'bg-bg-raised border border-border-dim text-txt-muted'
        )}>
          <span className={clsx('w-1.5 h-1.5 rounded-full', isRunning ? 'bg-accent-green pulse-dot' : 'bg-txt-muted')} />
          {isRunning ? 'agent running' : 'agent idle'}
        </div>
      </div>

      {/* Nav links */}
      <nav className="flex-1 px-3 py-3 flex flex-col gap-0.5">
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => clsx(
              'flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors',
              isActive
                ? 'bg-bg-raised text-txt-primary'
                : 'text-txt-muted hover:text-txt-secondary hover:bg-bg-raised'
            )}
          >
            <Icon size={15} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-border-dim">
        <p className="text-[10px] font-mono text-txt-muted">v1.0.0 · local</p>
      </div>
    </aside>
  )
}

// ── Inline SVG icons ──────────────────────────────────────────────────────────

function GridIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round">
      <rect x="1.5" y="1.5" width="5" height="5" rx="1.5"/>
      <rect x="9.5" y="1.5" width="5" height="5" rx="1.5"/>
      <rect x="1.5" y="9.5" width="5" height="5" rx="1.5"/>
      <rect x="9.5" y="9.5" width="5" height="5" rx="1.5"/>
    </svg>
  )
}

function ListIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round">
      <line x1="5" y1="4" x2="14" y2="4"/>
      <line x1="5" y1="8" x2="14" y2="8"/>
      <line x1="5" y1="12" x2="14" y2="12"/>
      <circle cx="2.5" cy="4" r="1" fill="currentColor" stroke="none"/>
      <circle cx="2.5" cy="8" r="1" fill="currentColor" stroke="none"/>
      <circle cx="2.5" cy="12" r="1" fill="currentColor" stroke="none"/>
    </svg>
  )
}

function UserIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round">
      <circle cx="8" cy="5.5" r="2.5"/>
      <path d="M2.5 14c0-3.038 2.462-5.5 5.5-5.5s5.5 2.462 5.5 5.5"/>
    </svg>
  )
}

function GearIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round">
      <circle cx="8" cy="8" r="2"/>
      <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.05 3.05l1.41 1.41M11.54 11.54l1.41 1.41M3.05 12.95l1.41-1.41M11.54 4.46l1.41-1.41"/>
    </svg>
  )
}