const DISPLAY_NAME = {
  market_scanner: 'Market Scanner',
  risk_gatekeeper: 'Risk Gatekeeper',
  execution: 'Execution Agent'
}

const STATUS_CONFIG = {
  running: {
    dot: 'bg-green pulse',
    text: 'text-green',
    badge: 'bg-green-dim text-green border-green/30',
    label: 'RUNNING'
  },
  stopped: {
    dot: 'bg-muted',
    text: 'text-muted',
    badge: 'bg-surface2 text-muted border-border',
    label: 'STOPPED'
  },
  error: {
    dot: 'bg-red pulse',
    text: 'text-red',
    badge: 'bg-red-dim text-red border-red/30',
    label: 'ERROR'
  }
}

export default function AgentCard({
  name,
  status,
  last_run,
  mode,
  onStart,
  onStop
}) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.stopped

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-border bg-surface2 p-4 transition-colors hover:border-border-hover lg:flex-row lg:items-center lg:justify-between">
      <div className="flex min-w-0 flex-wrap items-center gap-2 sm:gap-3">
        <span className={`h-2 w-2 rounded-full ${config.dot}`} />
        <span className="truncate font-mono text-sm font-semibold text-text">
          {DISPLAY_NAME[name] || name}
        </span>
        <span
          className={`rounded border px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest ${config.badge}`}
        >
          {config.label}
        </span>
      </div>

      <div className="min-w-0 flex-1 lg:px-4">
        <div className="font-mono text-[10px] text-muted">
          {last_run ? `Last: ${last_run}` : 'Never run'}
        </div>
        <div
          className={`mt-1 text-[9px] uppercase tracking-widest ${
            mode === 'live' ? 'text-green' : 'text-amber'
          }`}
        >
          {mode}
        </div>
      </div>

      <div className="flex w-full flex-col gap-2 self-start lg:w-auto lg:flex-row lg:self-auto">
        {status !== 'running' ? (
          <button
            type="button"
            onClick={onStart}
            className="w-full rounded border border-green/30 bg-green-dim px-3 py-1.5 font-mono text-[10px] font-bold uppercase tracking-wider text-green transition-colors hover:bg-green/20 lg:w-auto"
          >
            START
          </button>
        ) : null}

        {status === 'running' ? (
          <button
            type="button"
            onClick={onStop}
            className="w-full rounded border border-red/30 bg-red-dim px-3 py-1.5 font-mono text-[10px] font-bold uppercase tracking-wider text-red transition-colors hover:bg-red/20 lg:w-auto"
          >
            STOP
          </button>
        ) : null}
      </div>
    </div>
  )
}
