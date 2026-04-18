function formatNumber(value, digits = 2) {
  const num = Number(value)
  if (Number.isNaN(num)) return '—'
  return num.toFixed(digits)
}

export default function SignalDetail({ signal }) {
  const entry = Number(signal?.entry_price || 0)
  const target = Number(signal?.target || 0)
  const stoploss = Number(signal?.stoploss || 0)
  const qty = Number(signal?.qty || 0)
  const reward = target - entry
  const risk = entry - stoploss
  const rr = risk > 0 ? reward / risk : 0

  const rsiValue = Number(signal?.rsi)
  const rsiClass =
    rsiValue < 30 ? 'text-green' : rsiValue > 70 ? 'text-red' : 'text-text'

  const macdState = signal?.macd_state || '—'
  const macdClass =
    macdState === 'bullish_cross'
      ? 'text-green'
      : macdState === 'bullish'
        ? 'text-blue'
        : 'text-red'

  const confidence = Number(signal?.confidence || 0)
  const confidenceBarClass =
    confidence < 60 ? 'bg-red' : confidence <= 75 ? 'bg-amber' : 'bg-green'

  const riskStatus = signal?.risk_status || 'pending'
  const statusClass =
    riskStatus === 'approved'
      ? 'border-green/30 bg-green-dim text-green'
      : riskStatus === 'rejected'
        ? 'border-red/30 bg-red-dim text-red'
        : 'border-amber/30 bg-amber-dim text-amber'

  return (
    <div className="grid gap-4 rounded-lg border border-border bg-surface2 p-5 lg:grid-cols-4">
      <div>
        <div className="mb-3 font-mono text-[9px] uppercase tracking-wider text-muted">
          ENTRY DETAILS
        </div>
        <div className="space-y-2">
          <div className="mb-1 flex items-center justify-between border-b border-border/50 pb-1 text-[11px] font-mono">
            <span className="text-muted">Symbol</span>
            <span className="font-semibold text-text">{signal.symbol}</span>
          </div>
          <div className="mb-1 flex items-center justify-between border-b border-border/50 pb-1 text-[11px] font-mono">
            <span className="text-muted">Action</span>
            <span
              className={`rounded px-2 py-0.5 text-[9px] ${
                signal.action === 'SELL'
                  ? 'bg-red-dim text-red'
                  : 'bg-green-dim text-green'
              }`}
            >
              {signal.action}
            </span>
          </div>
          <div className="mb-1 flex items-center justify-between border-b border-border/50 pb-1 text-[11px] font-mono">
            <span className="text-muted">Entry</span>
            <span className="text-text">₹{formatNumber(entry)}</span>
          </div>
          <div className="mb-1 flex items-center justify-between border-b border-border/50 pb-1 text-[11px] font-mono">
            <span className="text-muted">Qty</span>
            <span className="text-text">{qty} shares</span>
          </div>
          <div className="flex items-center justify-between text-[11px] font-mono">
            <span className="text-muted">Value</span>
            <span className="text-text">₹{formatNumber(entry * qty)}</span>
          </div>
        </div>
      </div>

      <div>
        <div className="mb-3 font-mono text-[9px] uppercase tracking-wider text-muted">
          EXIT LEVELS
        </div>
        <div className="space-y-3 font-mono text-[11px]">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-muted">Target</span>
              <span className="font-semibold text-green">
                ₹{formatNumber(target)}
              </span>
            </div>
            <div className="mt-1 text-[10px] text-green">
              +{formatNumber(((target - entry) / entry) * 100)}%
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between">
              <span className="text-muted">Stoploss</span>
              <span className="font-semibold text-red">
                ₹{formatNumber(stoploss)}
              </span>
            </div>
            <div className="mt-1 text-[10px] text-red">
              -{formatNumber(((entry - stoploss) / entry) * 100)}%
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-muted">Risk:Reward</span>
            <span className={rr >= 1.5 ? 'text-green' : 'text-amber'}>
              {formatNumber(rr)}
            </span>
          </div>
        </div>
      </div>

      <div>
        <div className="mb-3 font-mono text-[9px] uppercase tracking-wider text-muted">
          INDICATORS
        </div>
        <div className="space-y-3 font-mono text-[11px]">
          <div className="flex items-center justify-between">
            <span className="text-muted">RSI(14)</span>
            <span className={rsiClass}>
              {signal?.rsi != null ? formatNumber(signal.rsi, 1) : '—'}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-muted">MACD</span>
            <span className={macdClass}>{macdState}</span>
          </div>

          <div>
            <div className="flex items-center justify-between">
              <span className="text-muted">Confidence</span>
              <span className="text-text">{confidence}%</span>
            </div>
            <div className="mt-1 h-1.5 w-full rounded-full bg-surface">
              <div
                className={`h-full rounded-full ${confidenceBarClass}`}
                style={{ width: `${Math.max(0, Math.min(confidence, 100))}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      <div>
        <div className="mb-3 font-mono text-[9px] uppercase tracking-wider text-muted">
          STATUS
        </div>
        <div
          className={`w-full rounded-lg border px-3 py-2 text-center font-mono text-xs font-bold ${statusClass}`}
        >
          {riskStatus === 'approved'
            ? '✓ APPROVED'
            : riskStatus === 'rejected'
              ? '✗ REJECTED'
              : '⏳ PENDING'}
        </div>

        {riskStatus === 'rejected' && signal?.reject_reason ? (
          <div className="mt-2 font-mono text-[10px] leading-relaxed text-red">
            {signal.reject_reason}
          </div>
        ) : null}

        <div
          className={`mt-3 font-mono text-[11px] ${
            signal?.executed ? 'text-green' : 'text-muted'
          }`}
        >
          {signal?.executed ? '✓ Executed' : '○ Not executed'}
        </div>

        <div
          className={`mt-1 font-mono text-[10px] uppercase ${
            signal?.mode === 'live' ? 'text-green' : 'text-amber'
          }`}
        >
          {signal?.mode || 'paper'}
        </div>

        <div className="mt-1 font-mono text-[10px] text-muted">
          {signal?.timestamp || '—'}
        </div>
      </div>
    </div>
  )
}
