function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value))
}

export default function PositionRow({
  position,
  onSquareOff,
  isSquaringOff
}) {
  const {
    id,
    symbol,
    exchange,
    qty,
    entry_price,
    ltp,
    pnl,
    pnl_pct,
    target,
    stoploss,
    mode,
    entry_time,
    gtt_order_id
  } = position

  const isUp = ltp > entry_price
  const isProfit = pnl >= 0
  const targetRange = target - entry_price
  const targetProgress =
    targetRange > 0 ? clamp(((ltp - entry_price) / targetRange) * 100, 0, 100) : 0

  return (
    <tr className="border-b border-border transition-colors hover:bg-surface2 last:border-0">
      <td className="whitespace-nowrap px-4 py-3 font-mono text-[11px]">
        <div className="flex flex-col gap-1">
          <span className="font-display text-sm font-bold text-text">
            {symbol}
          </span>
          <span className="hidden text-[9px] text-muted md:inline">{exchange}</span>
          <span
            className={`w-fit rounded border px-1.5 py-0.5 text-[9px] uppercase tracking-wider ${
              mode === 'live'
                ? 'border-green/30 bg-green-dim text-green'
                : 'border-amber/30 bg-amber-dim text-amber'
            }`}
          >
            {mode}
          </span>
        </div>
      </td>

      <td className="whitespace-nowrap px-4 py-3 font-mono text-[11px]">
        <div className="font-semibold text-text">{qty} shares</div>
        <div className="text-[10px] text-muted">MIS</div>
      </td>

      <td className="hidden whitespace-nowrap px-4 py-3 font-mono text-[11px] md:table-cell">
        <div className="text-text">₹{entry_price.toFixed(2)}</div>
        <div className="text-[10px] text-muted">avg price</div>
      </td>

      <td className="whitespace-nowrap px-4 py-3 font-mono text-[11px]">
        <div className={isUp ? 'text-green' : 'text-red'}>
          <span className="mr-1 inline-block h-1.5 w-1.5 rounded-full bg-green pulse" />
          ₹{ltp.toFixed(2)}
        </div>
      </td>

      <td className="whitespace-nowrap px-4 py-3 font-mono text-[11px]">
        <div className={`font-semibold ${isProfit ? 'text-green' : 'text-red'}`}>
          {isProfit ? '+' : ''}₹{pnl.toFixed(2)}
        </div>
        <div className={`text-[10px] ${isProfit ? 'text-green' : 'text-red'}`}>
          {isProfit ? '+' : ''}
          {pnl_pct.toFixed(2)}%
        </div>
      </td>

      <td className="hidden min-w-[140px] px-4 py-3 font-mono text-[11px] md:table-cell">
        <div className="flex flex-col gap-1">
          <div className="text-[10px] text-green">
            T: ₹{target.toFixed(2)}
            <div className="mt-0.5 h-0.5 w-full rounded bg-surface2">
              <div
                className="h-full rounded bg-green"
                style={{ width: `${targetProgress}%` }}
              />
            </div>
          </div>
          <div className="flex items-center gap-2 text-[10px] text-red">
            <span>SL: ₹{stoploss.toFixed(2)}</span>
            {gtt_order_id ? (
              <span className="rounded border border-blue/30 bg-blue-dim px-1 text-[8px] text-blue">
                GTT
              </span>
            ) : null}
          </div>
        </div>
      </td>

      <td className="hidden whitespace-nowrap px-4 py-3 font-mono text-[11px] text-muted md:table-cell">
        {entry_time || '—'}
      </td>

      <td className="whitespace-nowrap px-4 py-3 font-mono text-[11px]">
        <button
          type="button"
          onClick={() => onSquareOff(id)}
          disabled={isSquaringOff}
          className={`rounded border border-red/30 bg-red-dim px-3 py-1.5 font-mono text-[10px] font-bold uppercase tracking-wider text-red transition-colors hover:bg-red/20 ${
            isSquaringOff ? 'opacity-50' : ''
          }`}
        >
          {isSquaringOff ? '◌ Closing...' : 'SQUARE OFF'}
        </button>
      </td>
    </tr>
  )
}
