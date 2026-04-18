export default function MarginBar({ used, available, total }) {
  const safeTotal = total > 0 ? total : 1
  const usedPct = Math.max(0, Math.min(100, (used / safeTotal) * 100))

  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="mb-3 flex items-center justify-between">
        <span className="font-mono text-[10px] uppercase tracking-[3px] text-muted">
          MARGIN
        </span>
        <span className="font-mono text-[11px] text-green">
          {available.toFixed(2)} available
        </span>
      </div>

      <div className="mb-3 h-2 w-full rounded-full bg-surface2">
        <div
          className="h-full rounded-full bg-amber transition-all duration-500"
          style={{ width: `${usedPct.toFixed(1)}%` }}
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <div className="font-mono text-[9px] uppercase tracking-wider text-muted">
            USED
          </div>
          <div className="font-mono text-sm font-semibold text-text">
            ₹{used.toFixed(2)}
          </div>
        </div>
        <div>
          <div className="font-mono text-[9px] uppercase tracking-wider text-muted">
            AVAILABLE
          </div>
          <div className="font-mono text-sm font-semibold text-green">
            ₹{available.toFixed(2)}
          </div>
        </div>
        <div>
          <div className="font-mono text-[9px] uppercase tracking-wider text-muted">
            TOTAL
          </div>
          <div className="font-mono text-sm font-semibold text-text">
            ₹{total.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  )
}
