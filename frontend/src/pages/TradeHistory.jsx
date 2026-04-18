import { Fragment, useEffect, useMemo, useState } from 'react'

import {
  getTradeById,
  getTrades,
  getTradeStats
} from '../api/client'
import PnLChart from '../components/PnLChart'
import StatCard from '../components/StatCard'
import WinLossDonut from '../components/WinLossDonut'

const INPUT_CLASS =
  'w-full rounded border border-border bg-bg px-3 py-2 font-mono text-sm text-text transition-colors focus:border-border-hover focus:outline-none'
const LABEL_CLASS =
  'mb-1 block font-mono text-[10px] uppercase tracking-wider text-muted'

function SkeletonRow() {
  return <div className="mx-4 my-2 h-14 animate-pulse rounded bg-surface2" />
}

function formatCurrency(value) {
  if (value == null || Number.isNaN(value)) return '—'
  return `₹${Number(value).toFixed(2)}`
}

export default function TradeHistory() {
  const [trades, setTrades] = useState([])
  const [stats, setStats] = useState({})
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    mode: 'all',
    symbol: '',
    result: 'all',
    from: '',
    to: ''
  })
  const [expandedRow, setExpandedRow] = useState(null)
  const [expandedTrade, setExpandedTrade] = useState(null)
  const [loadingDetail, setLoadingDetail] = useState(false)

  useEffect(() => {
    getTradeStats()
      .then((response) => setStats(response.data || {}))
      .catch((error) => console.error(error))
  }, [])

  useEffect(() => {
    const timeout = setTimeout(() => {
      setLoading(true)
      getTrades({
        mode: filters.mode,
        symbol: filters.symbol,
        result: filters.result
      })
        .then((response) => {
          setTrades(response.data?.trades || [])
        })
        .catch((error) => {
          console.error(error)
          setTrades([])
        })
        .finally(() => setLoading(false))
    }, 300)

    return () => clearTimeout(timeout)
  }, [filters])

  const filteredTrades = useMemo(() => {
    return trades.filter((trade) => {
      const afterFrom = !filters.from || (trade.date || '') >= filters.from
      const beforeTo = !filters.to || (trade.date || '') <= filters.to
      return afterFrom && beforeTo
    })
  }, [filters.from, filters.to, trades])

  const winningTrades = useMemo(
    () => filteredTrades.filter((trade) => (trade.pnl || 0) > 0),
    [filteredTrades]
  )
  const losingTrades = useMemo(
    () => filteredTrades.filter((trade) => (trade.pnl || 0) < 0),
    [filteredTrades]
  )
  const totalPnl = useMemo(
    () => filteredTrades.reduce((sum, trade) => sum + (trade.pnl || 0), 0),
    [filteredTrades]
  )
  const winRate = filteredTrades.length
    ? (winningTrades.length / filteredTrades.length) * 100
    : 0

  const bestTrade = useMemo(() => {
    if (filteredTrades.length === 0) return null
    return [...filteredTrades].sort((a, b) => (b.pnl || 0) - (a.pnl || 0))[0]
  }, [filteredTrades])

  const worstTrade = useMemo(() => {
    if (filteredTrades.length === 0) return null
    return [...filteredTrades].sort((a, b) => (a.pnl || 0) - (b.pnl || 0))[0]
  }, [filteredTrades])

  const symbolPerformance = useMemo(() => {
    const grouped = filteredTrades.reduce((acc, trade) => {
      const symbol = trade.symbol || 'Unknown'
      if (!acc[symbol]) {
        acc[symbol] = {
          symbol,
          count: 0,
          wins: 0,
          totalPnl: 0
        }
      }
      acc[symbol].count += 1
      acc[symbol].wins += (trade.pnl || 0) > 0 ? 1 : 0
      acc[symbol].totalPnl += trade.pnl || 0
      return acc
    }, {})

    return Object.values(grouped)
      .map((item) => ({
        ...item,
        winRate: item.count > 0 ? (item.wins / item.count) * 100 : 0
      }))
      .sort((a, b) => b.totalPnl - a.totalPnl)
  }, [filteredTrades])

  const handleRowClick = async (tradeId) => {
    if (expandedRow === tradeId) {
      setExpandedRow(null)
      setExpandedTrade(null)
      return
    }

    setExpandedRow(tradeId)
    setLoadingDetail(true)
    try {
      const response = await getTradeById(tradeId)
      setExpandedTrade(response.data || null)
    } catch (error) {
      console.error(error)
      setExpandedTrade(null)
    } finally {
      setLoadingDetail(false)
    }
  }

  const resetFilters = () => {
    setFilters({
      mode: 'all',
      symbol: '',
      result: 'all',
      from: '',
      to: ''
    })
  }

  return (
    <div className="fade-in space-y-6">
      <div>
        <h1 className="font-display text-xl font-bold text-text">
          Trade History
        </h1>
        <p className="mt-0.5 font-mono text-xs text-muted">
          Closed trades and performance analytics
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="TOTAL TRADES"
          value={`${filteredTrades.length}`}
          sub={`${winningTrades.length}W / ${losingTrades.length}L`}
          accent="blue"
          icon="📊"
        />
        <StatCard
          label="WIN RATE"
          value={filteredTrades.length > 0 ? `${winRate.toFixed(1)}%` : '—'}
          sub={`based on ${filteredTrades.length} trades`}
          accent={winRate >= 50 ? 'green' : 'red'}
          icon={winRate >= 50 ? '🎯' : '📉'}
        />
        <StatCard
          label="TOTAL P&L"
          value={`${totalPnl >= 0 ? '+' : ''}₹${totalPnl.toFixed(2)}`}
          sub="across all trades"
          accent={totalPnl >= 0 ? 'green' : 'red'}
          icon={totalPnl >= 0 ? '💰' : '💸'}
        />
        <StatCard
          label="BEST TRADE"
          value={bestTrade ? `+₹${bestTrade.pnl.toFixed(2)}` : '—'}
          sub={
            bestTrade
              ? `${bestTrade.symbol} on ${bestTrade.date}`
              : 'no trades yet'
          }
          accent="green"
          icon="🏆"
        />
      </div>

      <div className="flex flex-col gap-4 rounded-lg border border-border bg-surface p-4 sm:flex-row sm:flex-wrap sm:items-end">
        <div className="w-full sm:w-32">
          <label className={LABEL_CLASS}>Symbol</label>
          <input
            type="text"
            placeholder="e.g. NHPC"
            value={filters.symbol}
            onChange={(e) =>
              setFilters((prev) => ({ ...prev, symbol: e.target.value }))
            }
            className={INPUT_CLASS}
          />
        </div>

        <div className="w-full sm:w-28">
          <label className={LABEL_CLASS}>Mode</label>
          <select
            value={filters.mode}
            onChange={(e) =>
              setFilters((prev) => ({ ...prev, mode: e.target.value }))
            }
            className={INPUT_CLASS}
          >
            <option value="all">All</option>
            <option value="paper">Paper</option>
            <option value="live">Live</option>
          </select>
        </div>

        <div className="w-full sm:w-28">
          <label className={LABEL_CLASS}>Result</label>
          <select
            value={filters.result}
            onChange={(e) =>
              setFilters((prev) => ({ ...prev, result: e.target.value }))
            }
            className={INPUT_CLASS}
          >
            <option value="all">All</option>
            <option value="winners">Winners</option>
            <option value="losers">Losers</option>
          </select>
        </div>

        <div className="w-full sm:w-36">
          <label className={LABEL_CLASS}>From</label>
          <input
            type="date"
            value={filters.from}
            onChange={(e) =>
              setFilters((prev) => ({ ...prev, from: e.target.value }))
            }
            className={INPUT_CLASS}
          />
        </div>

        <div className="w-full sm:w-36">
          <label className={LABEL_CLASS}>To</label>
          <input
            type="date"
            value={filters.to}
            onChange={(e) =>
              setFilters((prev) => ({ ...prev, to: e.target.value }))
            }
            className={INPUT_CLASS}
          />
        </div>

        <button
          type="button"
          onClick={resetFilters}
          className="rounded border border-border px-3 py-2 font-mono text-[10px] uppercase tracking-wider text-muted transition-colors hover:border-red/30 hover:text-red"
        >
          Reset
        </button>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-lg border border-border bg-surface p-5 lg:col-span-2">
          <div className="mb-4 font-mono text-[10px] uppercase tracking-[3px] text-muted">
            MONTHLY P&amp;L
          </div>
          <PnLChart trades={filteredTrades} />
        </div>

        <div className="rounded-lg border border-border bg-surface p-5">
          <div className="mb-2 font-mono text-[10px] uppercase tracking-[3px] text-muted">
            WIN / LOSS RATIO
          </div>
          <WinLossDonut
            wins={winningTrades.length}
            losses={losingTrades.length}
            total={filteredTrades.length}
          />
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-border bg-surface">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div className="font-mono text-[10px] uppercase tracking-[3px] text-muted">
            TRADE HISTORY
          </div>
          <div className="font-mono text-[11px] text-muted">
            {filteredTrades.length} trades
          </div>
        </div>

        {loading ? (
          <div className="py-2">
            <SkeletonRow />
            <SkeletonRow />
            <SkeletonRow />
            <SkeletonRow />
            <SkeletonRow />
          </div>
        ) : filteredTrades.length === 0 ? (
          <div className="p-12 text-center">
            <div className="mb-3 text-3xl">📋</div>
            <div className="font-display font-bold text-text">
              No trades found
            </div>
            <div className="mt-2 font-mono text-sm text-muted">
              Try adjusting filters or wait for the first paper trade to
              execute.
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="px-5 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted">Date</th>
                <th className="px-5 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted">Symbol</th>
                <th className="px-5 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted">Action</th>
                <th className="hidden px-5 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted md:table-cell">Qty</th>
                <th className="hidden px-5 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted md:table-cell">Entry</th>
                <th className="hidden px-5 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted md:table-cell">Exit</th>
                <th className="px-5 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted">P&amp;L</th>
                <th className="hidden px-5 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted md:table-cell">Duration</th>
                <th className="px-5 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted">Mode</th>
                <th className="px-5 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted"></th>
              </tr>
            </thead>
            <tbody>
              {filteredTrades.map((trade) => {
                const isExpanded = expandedRow === trade.id
                const pnlPositive = (trade.pnl || 0) >= 0

                return (
                  <Fragment key={trade.id}>
                    <tr
                      onClick={() => handleRowClick(trade.id)}
                      className={`cursor-pointer border-b border-border transition-colors hover:bg-surface2 ${
                        isExpanded ? 'bg-surface2' : ''
                      }`}
                    >
                      <td className="px-5 py-3 font-mono text-[11px] text-muted">
                        {trade.date}
                      </td>
                      <td className="px-5 py-3 font-mono text-[11px]">
                        <span className="font-semibold text-text">
                          {trade.symbol}
                        </span>
                        <span className="hidden text-[9px] text-muted md:block">
                          {trade.exchange || 'NSE'}
                        </span>
                      </td>
                      <td className="px-5 py-3 font-mono text-[11px]">
                        <span
                          className={`rounded px-2 py-0.5 text-[9px] ${
                            trade.action === 'SELL'
                              ? 'bg-red-dim text-red'
                              : 'bg-green-dim text-green'
                          }`}
                        >
                          {trade.action}
                        </span>
                      </td>
                      <td className="hidden px-5 py-3 font-mono text-[11px] text-text md:table-cell">
                        {trade.qty}
                      </td>
                      <td className="hidden px-5 py-3 font-mono text-[11px] text-text md:table-cell">
                        {formatCurrency(trade.entry_price)}
                      </td>
                      <td className="hidden px-5 py-3 font-mono text-[11px] text-text md:table-cell">
                        {trade.exit_price != null
                          ? formatCurrency(trade.exit_price)
                          : '—'}
                      </td>
                      <td className="px-5 py-3 font-mono text-[11px]">
                        <div
                          className={`font-semibold ${
                            pnlPositive ? 'text-green' : 'text-red'
                          }`}
                        >
                          {trade.pnl >= 0 ? '+' : ''}
                          {formatCurrency(trade.pnl)}
                        </div>
                        <div
                          className={`text-[10px] ${
                            pnlPositive ? 'text-green' : 'text-red'
                          }`}
                        >
                          {trade.pnl_pct >= 0 ? '+' : ''}
                          {trade.pnl_pct?.toFixed(2)}%
                        </div>
                      </td>
                      <td className="hidden px-5 py-3 font-mono text-[11px] text-muted md:table-cell">
                        {trade.duration || '—'}
                      </td>
                      <td className="px-5 py-3 font-mono text-[11px]">
                        <span
                          className={`rounded border px-2 py-0.5 text-[9px] uppercase tracking-wider ${
                            trade.mode === 'live'
                              ? 'border-green/30 bg-green-dim text-green'
                              : 'border-amber/30 bg-amber-dim text-amber'
                          }`}
                        >
                          {trade.mode}
                        </span>
                      </td>
                      <td className="px-5 py-3 font-mono text-[10px] text-muted">
                        {isExpanded ? '▼' : '▶'}
                      </td>
                    </tr>
                    {isExpanded ? (
                      <tr className="border-b border-border bg-surface2">
                        <td colSpan={10} className="px-5 py-4">
                          {loadingDetail ? (
                            <div className="font-mono text-[11px] text-muted">
                              Loading details...
                            </div>
                          ) : expandedTrade ? (
                            <div className="grid gap-6 md:grid-cols-3">
                              <div>
                                <div className="mb-2 font-mono text-[9px] uppercase tracking-wider text-muted">
                                  SIGNAL DETAILS
                                </div>
                                <div className="space-y-2 font-mono text-[11px]">
                                  <div className="flex justify-between gap-3">
                                    <span className="text-muted">RSI at entry</span>
                                    <span className="text-text">
                                      {expandedTrade.rsi ?? '—'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between gap-3">
                                    <span className="text-muted">Signal reason</span>
                                    <span className="text-right text-text">
                                      {expandedTrade.signal_reason || '—'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between gap-3">
                                    <span className="text-muted">Confidence</span>
                                    <span className="text-text">
                                      {expandedTrade.confidence != null
                                        ? `${expandedTrade.confidence}%`
                                        : '—'}
                                    </span>
                                  </div>
                                </div>
                              </div>

                              <div>
                                <div className="mb-2 font-mono text-[9px] uppercase tracking-wider text-muted">
                                  ORDER DETAILS
                                </div>
                                <div className="space-y-2 font-mono text-[11px]">
                                  <div className="flex justify-between gap-3">
                                    <span className="text-muted">Entry order ID</span>
                                    <span className="text-right text-text">
                                      {expandedTrade.entry_order_id || '—'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between gap-3">
                                    <span className="text-muted">Exit order ID</span>
                                    <span className="text-right text-text">
                                      {expandedTrade.exit_order_id || '—'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between gap-3">
                                    <span className="text-muted">Product</span>
                                    <span className="text-text">
                                      {expandedTrade.product || '—'}
                                    </span>
                                  </div>
                                </div>
                              </div>

                              <div>
                                <div className="mb-2 font-mono text-[9px] uppercase tracking-wider text-muted">
                                  P&amp;L BREAKDOWN
                                </div>
                                <div className="space-y-2 font-mono text-[11px]">
                                  <div className="flex justify-between gap-3">
                                    <span className="text-muted">Entry value</span>
                                    <span className="text-text">
                                      {formatCurrency(
                                        (expandedTrade.entry_price || 0) *
                                          (expandedTrade.qty || 0)
                                      )}
                                    </span>
                                  </div>
                                  <div className="flex justify-between gap-3">
                                    <span className="text-muted">Exit value</span>
                                    <span className="text-text">
                                      {expandedTrade.exit_price != null
                                        ? formatCurrency(
                                            expandedTrade.exit_price *
                                              (expandedTrade.qty || 0)
                                          )
                                        : '—'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between gap-3">
                                    <span className="text-muted">Gross P&amp;L</span>
                                    <span
                                      className={
                                        (expandedTrade.pnl || 0) >= 0
                                          ? 'text-green'
                                          : 'text-red'
                                      }
                                    >
                                      {expandedTrade.pnl >= 0 ? '+' : ''}
                                      {formatCurrency(expandedTrade.pnl)}
                                    </span>
                                  </div>
                                  <div className="flex justify-between gap-3">
                                    <span className="text-muted">Return</span>
                                    <span
                                      className={
                                        (expandedTrade.pnl_pct || 0) >= 0
                                          ? 'text-green'
                                          : 'text-red'
                                      }
                                    >
                                      {expandedTrade.pnl_pct >= 0 ? '+' : ''}
                                      {expandedTrade.pnl_pct?.toFixed(2) ?? '0.00'}%
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ) : (
                            <div className="font-mono text-[11px] text-muted">
                              No detail available
                            </div>
                          )}
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                )
              })}
            </tbody>
          </table>
          </div>
        )}
      </div>

      <div className="overflow-hidden rounded-lg border border-border bg-surface">
        <div className="border-b border-border px-5 py-4 font-mono text-[10px] uppercase tracking-[3px] text-muted">
          TOP SYMBOLS
        </div>

        {symbolPerformance.length === 0 ? (
          <div className="p-6 text-center font-mono text-sm text-muted">
            No data yet
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                {['Symbol', 'Trades', 'Wins', 'Win Rate', 'Total P&L'].map(
                  (heading) => (
                    <th
                      key={heading}
                      className="px-5 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted"
                    >
                      {heading}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody>
              {symbolPerformance.slice(0, 10).map((item) => (
                <tr
                  key={item.symbol}
                  className="border-b border-border transition-colors hover:bg-surface2 last:border-0"
                >
                  <td className="px-5 py-3 font-mono text-[11px] font-semibold text-text">
                    {item.symbol}
                  </td>
                  <td className="px-5 py-3 font-mono text-[11px] text-muted">
                    {item.count}
                  </td>
                  <td className="px-5 py-3 font-mono text-[11px] text-green">
                    {item.wins}
                  </td>
                  <td
                    className={`px-5 py-3 font-mono text-[11px] ${
                      item.winRate >= 50 ? 'text-green' : 'text-red'
                    }`}
                  >
                    {item.winRate.toFixed(0)}%
                  </td>
                  <td
                    className={`px-5 py-3 font-mono text-[11px] font-semibold ${
                      item.totalPnl >= 0 ? 'text-green' : 'text-red'
                    }`}
                  >
                    {item.totalPnl >= 0 ? '+' : ''}₹
                    {item.totalPnl.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
