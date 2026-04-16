export default function Settings() {
  return (
    <div className="p-6 max-w-2xl flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-light text-txt-primary tracking-tight">Settings</h1>
        <p className="text-[11px] font-mono text-txt-muted mt-0.5">API keys and portal credentials live in <code className="bg-bg-raised px-1 rounded text-accent-green">.env</code></p>
      </div>

      <div className="bg-bg-surface border border-border-dim rounded-xl p-5 flex flex-col gap-4">
        <p className="text-[10px] font-mono text-txt-muted uppercase tracking-wider">Configuration</p>

        <p className="text-sm text-txt-secondary leading-relaxed">
          Credentials are stored in <code className="bg-bg-raised px-1 rounded text-accent-green text-[11px]">backend/.env</code> and never exposed to the frontend. Edit that file directly:
        </p>

        <pre className="bg-bg-raised rounded-lg p-4 text-[11px] font-mono text-txt-secondary overflow-x-auto leading-relaxed">
{`# backend/.env

TINYFISH_API_KEY=tf_live_...
ANTHROPIC_API_KEY=sk-ant-...

INTERNSHALA_EMAIL=you@gmail.com
INTERNSHALA_PASSWORD=yourpassword

LINKEDIN_EMAIL=you@gmail.com
LINKEDIN_PASSWORD=yourpassword

NAUKRI_EMAIL=you@gmail.com
NAUKRI_PASSWORD=yourpassword

MAX_APPLICATIONS_PER_RUN=30`}
        </pre>

        <div className="bg-accent-amber2 border border-accent-amber/30 rounded-lg px-4 py-3">
          <p className="text-[11px] font-mono text-accent-amber">
            ⚠ Never commit .env to git. It is already in .gitignore.
          </p>
        </div>
      </div>

      <div className="bg-bg-surface border border-border-dim rounded-xl p-5 flex flex-col gap-3">
        <p className="text-[10px] font-mono text-txt-muted uppercase tracking-wider">Phase status</p>
        {[
          { phase: 'Phase 1', label: 'Backend + DB + Frontend',   done: true  },
          { phase: 'Phase 2', label: 'TinyFish agent integration', done: false },
          { phase: 'Phase 3', label: 'Portal agents (3 portals)',  done: false },
          { phase: 'Phase 4', label: 'Claude cover letters + JD parse', done: false },
        ].map(({ phase, label, done }) => (
          <div key={phase} className="flex items-center gap-3">
            <span className={`text-[10px] font-mono w-16 ${done ? 'text-accent-green' : 'text-txt-muted'}`}>
              {done ? '✓ done' : '· next'}
            </span>
            <span className="text-[11px] font-mono text-txt-muted">{phase}</span>
            <span className="text-[12px] text-txt-secondary">{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}