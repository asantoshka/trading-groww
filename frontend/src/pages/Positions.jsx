import { useCallback, useEffect, useState } from 'react'

import { closePosition, getMargin, getPositions } from '../api/client'
import MarginBar from '../components/MarginBar'
import PositionRow from '../components/PositionRow'
import useStore from '../store/useStore'

function SkeletonRow() {
  return <div className="h-12 animate-pulse rounded-lg bg-surface2" />
}

export default function Positions() {
  const [positions, setLocalPositions] = useState([])
  const [margin, setMargin] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [squaringOff, setSquaringOff] = useState({})
  const [lastUpdated, setLastUpdated] = useState(null)

  const wsConnected = useStore((s) => s.wsConnected)
  const storePositions = useStore((s) => s.positions)
  const updateLtp = useStore((s) => s.updateLtp)
  const setPositions = useStore((s) => s.setPositions)

  const loadPositions = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await getPositions()
      const nextPositions = response.data?.positions || []
      setPositions(nextPositions)
      setLocalPositions(nextPositions)
      setLastUpdated(new Date())
    } catch (err) {
      console.error(err)
      setError(err.message || 'Failed to load positions')
    } finally {
      setLoading(false)
    }
  }, [setPositions])

  const loadMargin = useCallback(async () => {
    try {
      const response = await getMargin()
      setMargin(response.data || {})
    } catch (err) {
      console.error(err)
    }
  }, [])

  useEffect(() => {
    loadPositions()
    loadMargin()

    const interval = setInterval(loadPositions, 30000)
    return () => clearInterval(interval)
  }, [loadMargin, loadPositions])

  useEffect(() => {
    positions.forEach((position) => {
      if (position?.ltp != null) {
        updateLtp(position.symbol, position.ltp)
      }
    })
  }, [positions, updateLtp])

  const displayPositions = positions.map((position) => {
    const storePos = storePositions.find((sp) => sp.symbol === position.symbol)
    return {
      ...position,
      ltp: storePos?.ltp ?? position.ltp ?? position.entry_price,
      pnl: storePos?.pnl ?? position.pnl ?? 0,
      pnl_pct: storePos?.pnl_pct ?? position.pnl_pct ?? 0
    }
  })

  const handleSquareOff = useCallback(
    async (positionId) => {
      const confirmed = window.confirm(
        'Are you sure you want to square off this position? This will place a market SELL order immediately.'
      )

      if (!confirmed) return

      setSquaringOff((prev) => ({ ...prev, [positionId]: true }))

      try {
        await closePosition(positionId)
        setLocalPositions((prev) => prev.filter((p) => p.id !== positionId))
        setPositions(storePositions.filter((p) => p.id !== positionId))
        console.log(`Position ${positionId} squared off successfully`)
      } catch (err) {
        console.error(err)
      } finally {
        setSquaringOff((prev) => ({ ...prev, [positionId]: false }))
      }
    },
    [setPositions, storePositions]
  )

  const totalPnl = displayPositions.reduce((sum, position) => sum + (position.pnl || 0), 0)
  const totalPnlPct =
    positions.length > 0
      ? (totalPnl /
          positions.reduce((sum, position) => sum + position.entry_price * position.qty, 0)) *
        100
      : 0

  const lastUpdatedText = lastUpdated
    ? lastUpdated.toLocaleTimeString('en-IN', {
        timeZone: 'Asia/Kolkata',
        hour12: false
      })
    : '—'

  return (
    <div className="fade-in space-y-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="font-display text-xl font-bold text-text">Live Positions</h1>
          <p className="mt-0.5 font-mono text-xs text-muted">
            Real-time position tracking
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <div className="font-mono text-[10px] text-muted">
            Updated: {lastUpdatedText}
          </div>
          <div
            className={`font-mono text-[10px] ${
              wsConnected ? 'text-green' : 'text-amber'
            }`}
          >
            ● {wsConnected ? 'Live' : 'Polling'}
          </div>
          <button
            type="button"
            onClick={loadPositions}
            className="rounded border border-border px-3 py-1.5 font-mono text-[10px] uppercase tracking-wider text-muted transition-colors hover:border-border-hover hover:text-text"
          >
            ↻ REFRESH
          </button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-border bg-surface p-4">
          <div className="font-mono text-[10px] uppercase tracking-[3px] text-muted">
            OPEN POSITIONS
          </div>
          <div className="font-display text-3xl font-bold text-text">
            {displayPositions.length}
          </div>
        </div>

        <div
          className={`rounded-lg border bg-surface p-4 shadow-lg ${
            totalPnl >= 0
              ? 'border-green/30 shadow-green/10'
              : 'border-red/30 shadow-red/10'
          }`}
        >
          <div className="font-mono text-[10px] uppercase tracking-[3px] text-muted">
            TOTAL P&amp;L
          </div>
          <div
            className={`font-display text-3xl font-bold ${
              totalPnl >= 0 ? 'text-green' : 'text-red'
            }`}
          >
            {totalPnl >= 0 ? '+' : ''}₹{totalPnl.toFixed(2)}
          </div>
          <div
            className={`mt-1 font-mono text-[11px] ${
              totalPnl >= 0 ? 'text-green' : 'text-red'
            }`}
          >
            {totalPnl >= 0 ? '+' : ''}
            {totalPnlPct.toFixed(2)}% overall
          </div>
        </div>

        <MarginBar
          used={margin.used_margin ?? margin.used ?? 0}
          available={margin.available_margin ?? margin.available ?? 5000}
          total={margin.total_margin ?? margin.total ?? 5000}
        />
      </div>

      <div>
        {loading ? (
          <div className="space-y-3">
            <SkeletonRow />
            <SkeletonRow />
            <SkeletonRow />
          </div>
        ) : error ? (
          <div className="rounded-lg border border-red/30 bg-red-dim p-4 font-mono text-sm text-red">
            {error}
          </div>
        ) : displayPositions.length === 0 ? (
          <div className="rounded-lg border border-border bg-surface p-16 text-center">
            <div className="mb-4 text-4xl">📋</div>
            <div className="font-display text-lg font-bold text-text">
              No Open Positions
            </div>
            <div className="mt-2 font-mono text-sm text-muted">
              The scanner is watching the market. Positions will appear here when
              orders are executed.
            </div>
            <div className="mt-4 font-mono text-[10px] text-muted">
              Auto square-off at 15:10 IST
            </div>
          </div>
        ) : (
          <div className="w-full overflow-x-auto rounded-lg border border-border bg-surface">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted">
                    Symbol
                  </th>
                  <th className="px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted">
                    Qty
                  </th>
                  <th className="hidden px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted md:table-cell">
                    Entry
                  </th>
                  <th className="px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted">
                    LTP
                  </th>
                  <th className="px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted">
                    P&amp;L
                  </th>
                  <th className="hidden px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted md:table-cell">
                    Target/SL
                  </th>
                  <th className="hidden px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted md:table-cell">
                    Time
                  </th>
                  <th className="px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody>
                {displayPositions.map((position) => (
                  <PositionRow
                    key={position.id}
                    position={position}
                    onSquareOff={handleSquareOff}
                    isSquaringOff={squaringOff[position.id] || false}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-2 font-mono text-[10px] text-muted md:flex-row md:items-center md:justify-between">
        <span>MIS positions auto square-off at 15:10 IST</span>
        <span>LTP updates every 30s via polling | Real-time via WebSocket when connected</span>
      </div>
    </div>
  )
}
