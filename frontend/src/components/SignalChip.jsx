const RISK_CLASSES = {
  approved: 'bg-green-dim text-green border-green/30',
  rejected: 'bg-red-dim text-red border-red/30',
  pending: 'bg-amber-dim text-amber border-amber/30'
}

export default function SignalChip({ signal }) {
  const confidence = Number(signal?.confidence ?? 0)
  const riskStatus = signal?.risk_status || 'pending'
  const riskClasses = RISK_CLASSES[riskStatus] || RISK_CLASSES.pending
  const barClass =
    confidence < 60 ? 'bg-red' : confidence <= 75 ? 'bg-amber' : 'bg-green'

  return (
    <div className="min-w-0 flex-shrink-0 rounded-lg border border-border bg-surface2 p-3 transition-colors hover:border-border-hover flex items-center gap-4">
      <div className="flex-shrink-0">
        <div className="font-display text-sm font-bold text-text">
          {signal?.symbol || '--'}
        </div>
        <span
          className={`mt-1 inline-block rounded px-1.5 py-0.5 text-[9px] ${
            signal?.action === 'SELL'
              ? 'bg-red-dim text-red'
              : 'bg-green-dim text-green'
          }`}
        >
          {signal?.action || 'BUY'}
        </span>
      </div>

      <div className="flex-1">
        <div className="font-mono text-[11px] text-muted">
          ₹{Number(signal?.entry_price ?? 0).toFixed(2)}
        </div>
        <div className="font-mono text-[10px] text-muted">
          RSI {signal?.rsi ?? '--'}
        </div>
      </div>

      <div className="w-16 flex-shrink-0">
        <div className="text-[9px] text-muted">Conf</div>
        <div className="mt-0.5 h-1 w-full rounded-full bg-muted2">
          <div
            className={`h-1 rounded-full ${barClass}`}
            style={{ width: `${Math.max(0, Math.min(confidence, 100))}%` }}
          />
        </div>
      </div>

      <div
        className={`flex-shrink-0 rounded border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider ${riskClasses}`}
      >
        {riskStatus}
      </div>

      <div
        className={`flex-shrink-0 text-[11px] ${
          signal?.executed ? 'text-green' : 'text-muted'
        }`}
      >
        {signal?.executed ? '✓' : '○'}
      </div>
    </div>
  )
}
