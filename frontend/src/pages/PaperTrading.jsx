import { useCallback, useEffect, useMemo, useState } from 'react'

import {
  getPositions,
  getSignals,
  getTrades,
  getTradeStats,
  triggerScan
} from '../api/client'
import StatCard from '../components/StatCard'
import useStore from '../store/useStore'

function formatCurrency(value) {
  const num = Number(value || 0)
  return `₹${num.toFixed(2)}`
}

export default function PaperTrading() {
  const [paperTrades, setPaperTrades] = useState([])
  const [liveTrades, setLiveTrades] = useState([])
  const [paperStats, setPaperStats] = useState({})
  const [paperPositions, setPaperPositions] = useState([])
  const [paperSignals, setPaperSignals] = useState([])
  const [loading, setLoading] = useState(true)
  const [resetting, setResetting] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [triggering, setTriggering] = useState(false)
  const [triggerSuccess, setTriggerSuccess] = useState(false)
  const [showResetConfirm, setShowResetConfirm] = useState(false)

  const mode = useStore((s) => s.mode)
  const storePositions = useStore((s) => s.positions)

  const loadPaperData = useCallback(async () => {
    setLoading(true)
    try {
      const [paperTradesRes, liveTradesRes, tradeStatsRes, positionsRes, signalsRes] =
        await Promise.all([
          getTrades({ mode: 'paper' }),
          getTrades({ mode: 'live' }),
          getTradeStats(),
          getPositions(),
          getSignals({ mode: 'paper' })
        ])

      setPaperTrades(paperTradesRes.data?.trades || [])
      setLiveTrades(liveTradesRes.data?.trades || [])
      setPaperStats(tradeStatsRes.data || {})
      setPaperPositions(
        (positionsRes.data?.positions || []).filter((position) => position.mode === 'paper')
      )
      setPaperSignals(signalsRes.data?.signals || [])
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadPaperData()
  }, [loadPaperData])

  const displayPaperPositions = useMemo(() => {
    return paperPositions.map((position) => {
      const storePosition = storePositions.find((item) => item.symbol === position.symbol)
      return {
        ...position,
        ltp: storePosition?.ltp ?? position.ltp ?? position.entry_price,
        pnl: storePosition?.pnl ?? position.pnl ?? 0,
        pnl_pct: storePosition?.pnl_pct ?? position.pnl_pct ?? 0
      }
    })
  }, [paperPositions, storePositions])

  const paperWins = useMemo(
    () => paperTrades.filter((trade) => (trade.pnl || 0) > 0),
    [paperTrades]
  )
  const paperLosses = useMemo(
    () => paperTrades.filter((trade) => (trade.pnl || 0) < 0),
    [paperTrades]
  )
  const paperTotalPnl = useMemo(
    () => paperTrades.reduce((sum, trade) => sum + (trade.pnl || 0), 0),
    [paperTrades]
  )
  const paperWinRate = paperTrades.length > 0 ? (paperWins.length / paperTrades.length) * 100 : 0
  const avgPnlPerTrade = paperTrades.length > 0 ? paperTotalPnl / paperTrades.length : 0
  const avgWin = paperWins.length > 0 ? paperWins.reduce((sum, trade) => sum + trade.pnl, 0) / paperWins.length : 0
  const avgLoss =
    paperLosses.length > 0
      ? paperLosses.reduce((sum, trade) => sum + trade.pnl, 0) / paperLosses.length
      : 0
  const profitFactor = avgLoss !== 0 ? Math.abs(avgWin / avgLoss) : 0
  const openPnl = displayPaperPositions.reduce((sum, position) => sum + (position.pnl || 0), 0)
  const totalReturn = ((paperTotalPnl + openPnl) / 5000) * 100

  const liveTotalPnl = useMemo(
    () => liveTrades.reduce((sum, trade) => sum + (trade.pnl || 0), 0),
    [liveTrades]
  )

  const handleForceScan = async () => {
    setTriggering(true)
    try {
      await triggerScan()
      setTriggerSuccess(true)
      setTimeout(() => setTriggerSuccess(false), 3000)
    } catch (error) {
      console.error(error)
    } finally {
      setTriggering(false)
    }
  }

  const handleExportCSV = () => {
    setExporting(true)
    try {
      const headers = [
        'Date',
        'Symbol',
        'Action',
        'Qty',
        'Entry',
        'Exit',
        'PnL',
        'PnL%',
        'Duration',
        'Signal Reason'
      ]
      const rows = paperTrades.map((trade) =>
        [
          trade.date,
          trade.symbol,
          trade.action,
          trade.qty,
          trade.entry_price,
          trade.exit_price,
          trade.pnl,
          trade.pnl_pct,
          trade.duration,
          trade.signal_reason
        ].join(',')
      )
      const csv = [headers.join(','), ...rows].join('\n')
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = `paper-trades-${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(anchor)
      anchor.click()
      document.body.removeChild(anchor)
      URL.revokeObjectURL(url)
    } finally {
      setExporting(false)
    }
  }

  const handleResetConfirm = () => {
    setResetting(true)
    setPaperTrades([])
    setLiveTrades([])
    setPaperPositions([])
    setPaperSignals([])
    setShowResetConfirm(false)
    setResetting(false)
  }

  const executedSignals = paperSignals.filter((signal) => signal.executed).length

  return (
    <div className="fade-in space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-xl font-bold text-text">Paper Trading</h1>
          <p className="mt-0.5 font-mono text-xs text-muted">
            Strategy validation with real market data
          </p>
        </div>

        <div className="flex w-full flex-col items-stretch gap-3 sm:w-auto sm:flex-row sm:flex-wrap sm:items-center">
          <button
            type="button"
            onClick={handleForceScan}
            disabled={triggering}
            className={`rounded border px-4 py-2 font-mono text-[11px] font-bold uppercase tracking-wider transition-all duration-200 ${
              triggerSuccess
                ? 'border-green/30 bg-green-dim text-green'
                : 'border-blue/30 bg-blue-dim text-blue hover:bg-blue/20'
            } ${triggering ? 'opacity-60' : ''}`}
          >
            {triggerSuccess ? '✓ Scan Triggered' : triggering ? 'Scanning...' : '▶ Force Scan'}
          </button>

          <button
            type="button"
            onClick={handleExportCSV}
            disabled={paperTrades.length === 0 || exporting}
            className="rounded border border-border bg-surface2 px-4 py-2 font-mono text-[11px] font-bold uppercase tracking-wider text-muted transition-colors hover:border-border-hover hover:text-text disabled:opacity-40"
          >
            {exporting ? 'Exporting...' : '↓ Export CSV'}
          </button>

          <button
            type="button"
            onClick={() => setShowResetConfirm(true)}
            className="rounded border border-red/30 bg-red-dim px-4 py-2 font-mono text-[11px] font-bold uppercase tracking-wider text-red transition-colors hover:bg-red/20"
          >
            ⚠ Reset Paper
          </button>
        </div>
      </div>

      {showResetConfirm ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="mx-4 w-full max-w-sm rounded-xl border border-red/40 bg-surface p-8">
            <div className="mb-3 text-center text-3xl">⚠️</div>
            <div className="mb-2 text-center font-display text-lg font-bold text-red">
              Reset Paper Account?
            </div>
            <div className="mb-6 text-center font-mono text-sm text-muted">
              This will clear all paper trade history from this session. This cannot be undone.
            </div>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setShowResetConfirm(false)}
                className="flex-1 rounded border border-border px-4 py-2 font-mono text-[11px] text-muted"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleResetConfirm}
                className="flex-1 rounded border border-red/30 bg-red-dim px-4 py-2 font-mono text-[11px] font-bold text-red transition-colors hover:bg-red/20"
              >
                {resetting ? 'Resetting...' : 'Reset'}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="PAPER CAPITAL"
          value="₹5,000"
          sub="Starting balance"
          accent="blue"
          icon="🧪"
        />
        <StatCard
          label="TOTAL RETURN"
          value={`${totalReturn >= 0 ? '+' : ''}${totalReturn.toFixed(2)}%`}
          sub={`${paperTotalPnl >= 0 ? '+' : ''}₹${paperTotalPnl.toFixed(2)} P&L`}
          accent={totalReturn >= 0 ? 'green' : 'red'}
          icon={totalReturn >= 0 ? '📈' : '📉'}
        />
        <StatCard
          label="WIN RATE"
          value={paperTrades.length > 0 ? `${paperWinRate.toFixed(1)}%` : '—'}
          sub={`${paperWins.length}W / ${paperLosses.length}L`}
          accent={paperWinRate >= 50 ? 'green' : 'red'}
          icon="🎯"
        />
        <StatCard
          label="PROFIT FACTOR"
          value={profitFactor > 0 ? `${profitFactor.toFixed(2)}x` : '—'}
          sub="avg win / avg loss ratio"
          accent={profitFactor >= 1.5 ? 'green' : 'amber'}
          icon="⚖️"
        />
      </div>

      {liveTrades.length > 0 ? (
        <div className="rounded-lg border border-border bg-surface p-5">
          <div className="mb-4 font-mono text-[10px] uppercase tracking-[3px] text-muted">
            PAPER VS LIVE P&amp;L
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-muted">
                PAPER
              </div>
              <div className={`font-display text-2xl font-bold ${paperTotalPnl >= 0 ? 'text-green' : 'text-red'}`}>
                {paperTotalPnl >= 0 ? '+' : ''}{formatCurrency(paperTotalPnl)}
              </div>
            </div>
            <div>
              <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-muted">
                LIVE
              </div>
              <div className={`font-display text-2xl font-bold ${liveTotalPnl >= 0 ? 'text-green' : 'text-red'}`}>
                {liveTotalPnl >= 0 ? '+' : ''}{formatCurrency(liveTotalPnl)}
              </div>
            </div>
          </div>
        </div>
      ) : null}

      <div className="rounded-lg border border-border bg-surface p-5">
        <div className="mb-4 font-mono text-[10px] uppercase tracking-[3px] text-muted">
          PERFORMANCE BREAKDOWN
        </div>
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
          <div>
            <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-muted">Avg P&amp;L per Trade</div>
            <div className={`font-display text-xl font-bold ${avgPnlPerTrade >= 0 ? 'text-green' : 'text-red'}`}>
              {avgPnlPerTrade >= 0 ? '+' : ''}{formatCurrency(avgPnlPerTrade)}
            </div>
          </div>
          <div>
            <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-muted">Avg Winning Trade</div>
            <div className="font-display text-xl font-bold text-green">+{formatCurrency(avgWin)}</div>
          </div>
          <div>
            <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-muted">Avg Losing Trade</div>
            <div className="font-display text-xl font-bold text-red">{formatCurrency(avgLoss)}</div>
          </div>
          <div>
            <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-muted">Open P&amp;L</div>
            <div className={`font-display text-xl font-bold ${openPnl >= 0 ? 'text-green' : 'text-red'}`}>
              {openPnl >= 0 ? '+' : ''}{formatCurrency(openPnl)}
            </div>
          </div>
          <div>
            <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-muted">Total Trades</div>
            <div className="font-display text-xl font-bold text-text">{paperTrades.length}</div>
          </div>
          <div>
            <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-muted">Open Positions</div>
            <div className="font-display text-xl font-bold text-text">{displayPaperPositions.length}</div>
          </div>
          <div>
            <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-muted">Signals Generated</div>
            <div className="font-display text-xl font-bold text-text">{paperSignals.length}</div>
          </div>
          <div>
            <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-muted">Signals Executed</div>
            <div className="font-display text-xl font-bold text-text">{executedSignals}</div>
          </div>
        </div>
      </div>

      {displayPaperPositions.length > 0 ? (
        <div>
          <div className="mb-3 font-mono text-[10px] uppercase tracking-[3px] text-muted">
            OPEN PAPER POSITIONS
          </div>
          <div className="overflow-hidden rounded-lg border border-border bg-surface">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  {['Symbol', 'Qty', 'Entry', 'LTP', 'P&L', 'Target', 'SL'].map((heading) => (
                    <th
                      key={heading}
                      className="px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted"
                    >
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {displayPaperPositions.map((position) => (
                  <tr
                    key={position.id}
                    className="border-b border-border transition-colors hover:bg-surface2 last:border-0"
                  >
                    <td className="px-4 py-3 font-mono text-[11px] font-semibold text-text">
                      {position.symbol}
                    </td>
                    <td className="px-4 py-3 font-mono text-[11px] text-text">{position.qty}</td>
                    <td className="px-4 py-3 font-mono text-[11px] text-text">{formatCurrency(position.entry_price)}</td>
                    <td className={`px-4 py-3 font-mono text-[11px] ${Number(position.ltp) > Number(position.entry_price) ? 'text-green' : 'text-red'}`}>
                      {position.ltp != null ? formatCurrency(position.ltp) : '—'}
                    </td>
                    <td className={`px-4 py-3 font-mono text-[11px] font-semibold ${(position.pnl || 0) >= 0 ? 'text-green' : 'text-red'}`}>
                      {(position.pnl || 0) >= 0 ? '+' : ''}{formatCurrency(position.pnl)}
                    </td>
                    <td className="px-4 py-3 font-mono text-[11px] text-green">{formatCurrency(position.target)}</td>
                    <td className="px-4 py-3 font-mono text-[11px] text-red">{formatCurrency(position.stoploss)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      <div>
        <div className="mb-3 flex items-center justify-between">
          <div className="font-mono text-[10px] uppercase tracking-[3px] text-muted">
            PAPER TRADE HISTORY
          </div>
          <div className="font-mono text-[11px] text-muted">{paperTrades.length} trades</div>
        </div>

        {loading ? (
          <div className="rounded-lg border border-border bg-surface p-12 text-center font-mono text-sm text-muted">
            Loading paper account...
          </div>
        ) : paperTrades.length === 0 ? (
          <div className="rounded-lg border border-border bg-surface p-12 text-center">
            <div className="mb-3 text-3xl">🧪</div>
            <div className="font-display text-lg font-bold text-text">No paper trades yet</div>
            <div className="mt-2 font-mono text-sm text-muted">
              Paper trades will appear here after the scanner finds and executes a signal.
            </div>
            <div className="mt-4 rounded-lg border border-blue/30 bg-blue-dim p-3 font-mono text-[11px] text-blue">
              💡 Tip: Lower RSI threshold in Agent Control to generate more signals, or click Force Scan to trigger a manual scan.
            </div>
          </div>
        ) : (
          <div className="overflow-hidden rounded-lg border border-border bg-surface">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  {['Date', 'Symbol', 'Action', 'Qty', 'Entry', 'Exit', 'P&L', 'Return', 'Duration', 'Reason'].map((heading) => (
                    <th
                      key={heading}
                      className="px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted"
                    >
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {paperTrades.map((trade) => (
                  <tr
                    key={trade.id}
                    className="border-b border-border transition-colors hover:bg-surface2 last:border-0"
                  >
                    <td className="px-4 py-3 font-mono text-[10px] text-muted">{trade.date}</td>
                    <td className="px-4 py-3 font-mono text-sm font-semibold text-text">{trade.symbol}</td>
                    <td className="px-4 py-3 font-mono text-[11px]">
                      <span className={`rounded px-1.5 py-0.5 text-[9px] ${trade.action === 'SELL' ? 'bg-red-dim text-red' : 'bg-green-dim text-green'}`}>
                        {trade.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-[11px] text-text">{trade.qty}</td>
                    <td className="px-4 py-3 font-mono text-[11px] text-text">{formatCurrency(trade.entry_price)}</td>
                    <td className="px-4 py-3 font-mono text-[11px] text-muted">
                      {trade.exit_price != null ? formatCurrency(trade.exit_price) : '—'}
                    </td>
                    <td className={`px-4 py-3 font-mono text-[11px] font-semibold ${(trade.pnl || 0) >= 0 ? 'text-green' : 'text-red'}`}>
                      {(trade.pnl || 0) >= 0 ? '+' : ''}{formatCurrency(trade.pnl)}
                    </td>
                    <td className={`px-4 py-3 font-mono text-[10px] ${(trade.pnl_pct || 0) >= 0 ? 'text-green' : 'text-red'}`}>
                      {(trade.pnl_pct || 0) >= 0 ? '+' : ''}{Number(trade.pnl_pct || 0).toFixed(2)}%
                    </td>
                    <td className="px-4 py-3 font-mono text-[11px] text-muted">{trade.duration || '—'}</td>
                    <td
                      className="max-w-[150px] truncate px-4 py-3 font-mono text-[10px] text-muted"
                      title={trade.signal_reason || '—'}
                    >
                      {trade.signal_reason || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {paperTrades.length === 0 && displayPaperPositions.length === 0 ? (
        <div className="rounded-lg border border-border bg-surface p-6">
          <div className="mb-4 font-mono text-[10px] uppercase tracking-[3px] text-muted">
            GETTING STARTED
          </div>
          <div className="grid gap-4 lg:grid-cols-3">
            <div className="rounded-lg bg-surface2 p-4">
              <div className="mb-2 text-2xl">1️⃣</div>
              <div className="mb-1 font-display text-sm font-bold text-text">Lower RSI Threshold</div>
              <div className="font-mono text-[11px] text-muted">
                Go to Agent Control → Config → set RSI Oversold to 45-50 to get more frequent signals in ranging markets.
              </div>
            </div>
            <div className="rounded-lg bg-surface2 p-4">
              <div className="mb-2 text-2xl">2️⃣</div>
              <div className="mb-1 font-display text-sm font-bold text-text">Trigger a Manual Scan</div>
              <div className="font-mono text-[11px] text-muted">
                Click Force Scan above or go to Agent Control and click Trigger Scan. Best results during market hours 9:15 AM - 3:30 PM IST.
              </div>
            </div>
            <div className="rounded-lg bg-surface2 p-4">
              <div className="mb-2 text-2xl">3️⃣</div>
              <div className="mb-1 font-display text-sm font-bold text-text">Watch the Live Feed</div>
              <div className="font-mono text-[11px] text-muted">
                Open the Dashboard to see the real-time log stream as the scanner analyses each symbol and Claude makes its decision.
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
