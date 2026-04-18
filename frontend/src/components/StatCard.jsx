const ACCENTS = {
  green: {
    border: 'border-green/30',
    glow: 'shadow-green/10',
    label: 'text-green'
  },
  amber: {
    border: 'border-amber/30',
    glow: 'shadow-amber/10',
    label: 'text-amber'
  },
  blue: {
    border: 'border-blue/30',
    glow: 'shadow-blue/10',
    label: 'text-blue'
  },
  red: {
    border: 'border-red/30',
    glow: 'shadow-red/10',
    label: 'text-red'
  }
}

export default function StatCard({ label, value, sub, accent, icon }) {
  const theme = ACCENTS[accent] || ACCENTS.blue

  return (
    <div
      className={[
        'cursor-default rounded-lg border bg-surface p-5 shadow-lg transition-all duration-200 hover:border-border-hover',
        theme.border,
        theme.glow
      ].join(' ')}
    >
      <div className="flex items-start justify-between">
        <div
          className={[
            'font-mono text-[10px] uppercase tracking-[3px]',
            theme.label
          ].join(' ')}
        >
          {label}
        </div>
        <div className="text-xl" aria-hidden="true">
          {icon}
        </div>
      </div>

      <div className="mt-3 whitespace-nowrap font-display text-2xl font-bold text-text">
        {value}
      </div>

      <div className="mt-1 font-mono text-[11px] text-muted">{sub}</div>
    </div>
  )
}
