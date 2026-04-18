import { useCallback, useEffect, useMemo, useState } from 'react'

import {
  getSignalAnalytics,
  getSignals,
  getTodaySignals,
  injectSignal
} from '../api/client'
import SignalChip from '../components/SignalChip'
import SignalDetail from '../components/SignalDetail'
import StatCard from '../components/StatCard'
import useStore from '../store/useStore'

const INPUT_CLASS =
  'w-full rounded border border-border bg-bg px-3 py-2 font-mono text-sm text-text transition-colors focus:border-border-hover focus:outline-none'
const LABEL_CLASS =
  'mb-1 block font-mono text-[10px] uppercase tracking-wider text-muted'

function statusBadgeClass(status) {
  if (status === 'approved') return 'border-green/30 bg-green-dim text-green'
  if (status === 'rejected') return 'border-red/30 bg-red-dim text-red'
  return 'border-amber/30 bg-amber-dim text-amber'
}

function macdLabel(signal) {
  const state = signal?.macd_state
  if (state === 'bullish_cross') return '↑×'
  if (state === 'bullish') return '↑'
  if (state === 'bearish_cross') return '↓×'
  return '↓'
}

function macdClass(state) {
  return state?.includes('bullish') ? 'text-green' : 'text-red'
}

export default function Signals() {
  const [todaySignals, setTodaySignals] = useState([])
  const [allSignals, setAllSignals] = useState([])
  const [analytics, setAnalytics] = useState({})
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState({ mode: 'all', status: 'all' })
  const [showInjectForm, setShowInjectForm] = useState(false)
  const [injectForm, setInjectForm] = useState({
    symbol: '',
    action: 'BUY',
    entry_price: '',
    target: '',
    stoploss: '',
    qty: ''
  })
  const [injecting, setInjecting] = useState(false)
  const [injectError, setInjectError] = useState(null)
  const [injectSuccess, setInjectSuccess] = useState(false)
  const [expandedSignal, setExpandedSignal] = useState(null)

  const storeSignals = useStore((s) => s.signals)
  const addSignal = useStore((s) => s.addSignal)
  const mode = useStore((s) => s.mode)

  const loadTodaySignals = useCallback(async () => {
    const response = await getTodaySignals()
    setTodaySignals(response.data?.signals || [])
  }, [])

  const loadAllSignals = useCallback(async () => {
    const response = await getSignals({ mode: filter.mode })
    let nextSignals = response.data?.signals || []
    if (filter.status !== 'all') {
      nextSignals = nextSignals.filter(
        (signal) => (signal.risk_status || 'pending') === filter.status
      )
    }
    setAllSignals(nextSignals)
  }, [filter.mode, filter.status])

  const loadAnalytics = useCallback(async () => {
    const response = await getSignalAnalytics()
    setAnalytics(response.data || {})
  }, [])

  useEffect(() => {
    setLoading(true)
    Promise.all([loadTodaySignals(), loadAllSignals(), loadAnalytics()])
      .catch((error) => console.error(error))
      .finally(() => setLoading(false))
  }, [loadAllSignals, loadAnalytics, loadTodaySignals])

  useEffect(() => {
    loadAllSignals().catch((error) => console.error(error))
  }, [filter, loadAllSignals])

  const displayTodaySignals = useMemo(() => {
    const ids = new Set(storeSignals.map((signal) => signal.id))
    return [
      ...storeSignals,
      ...todaySignals.filter((signal) => !ids.has(signal.id))
    ]
  }, [storeSignals, todaySignals])

  const handleInject = async () => {
    const entry = Number(injectForm.entry_price)
    const target = Number(injectForm.target)
    const stoploss = Number(injectForm.stoploss)
    const qty = Number(injectForm.qty)

    if (!injectForm.symbol.trim()) {
      setInjectError('Symbol is required')
      return
    }
    if (entry <= 0 || target <= 0 || stoploss <= 0 || qty <= 0) {
      setInjectError('Entry, target, stoploss and quantity must be greater than 0')
      return
    }
    if (injectForm.action === 'BUY' && target <= entry) {
      setInjectError('For BUY signals, target must be greater than entry')
      return
    }
    if (injectForm.action === 'BUY' && stoploss >= entry) {
      setInjectError('For BUY signals, stoploss must be lower than entry')
      return
    }

    setInjecting(true)
    setInjectError(null)

    try {
      const response = await injectSignal({
        ...injectForm,
        symbol: injectForm.symbol.trim().toUpperCase(),
        entry_price: entry,
        target,
        stoploss,
        qty
      })
      addSignal(response.data.signal)
      setInjectSuccess(true)
      setTimeout(() => {
        setInjectSuccess(false)
        setShowInjectForm(false)
        setInjectForm({
          symbol: '',
          action: 'BUY',
          entry_price: '',
          target: '',
          stoploss: '',
          qty: ''
        })
      }, 2000)
    } catch (error) {
      setInjectError(error.message || 'Failed to inject signal')
    } finally {
      setInjecting(false)
    }
  }

  const approvedCount = analytics.approved || 0
  const analyticsTotal = analytics.total || 0
  const approvalRate =
    analyticsTotal > 0 ? ((approvedCount / analyticsTotal) * 100).toFixed(0) : '0'
  const maxRejectCount = Math.max(
    ...(analytics.rejection_reasons || []).map((reason) => reason.count),
    1
  )

  const upside =
    injectForm.entry_price && injectForm.target
      ? (
          ((Number(injectForm.target) - Number(injectForm.entry_price)) /
            Number(injectForm.entry_price)) *
          100
        ).toFixed(2)
      : null
  const downside =
    injectForm.entry_price && injectForm.stoploss
      ? (
          ((Number(injectForm.entry_price) - Number(injectForm.stoploss)) /
            Number(injectForm.entry_price)) *
          100
        ).toFixed(2)
      : null
  const tradeValue =
    injectForm.entry_price && injectForm.qty
      ? (Number(injectForm.entry_price) * Number(injectForm.qty)).toFixed(2)
      : null

  return (
    <div className="fade-in space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-xl font-bold text-text">Signals</h1>
          <p className="mt-0.5 font-mono text-xs text-muted">
            Scanner signals and manual injection
          </p>
        </div>

        {mode === 'paper' ? (
          <button
            type="button"
            onClick={() => setShowInjectForm((prev) => !prev)}
            className={`w-full rounded border px-4 py-2 font-mono text-[11px] font-bold uppercase tracking-wider transition-all sm:w-auto ${
              showInjectForm
                ? 'border-border bg-surface2 text-muted'
                : 'border-blue/30 bg-blue-dim text-blue hover:bg-blue/20'
            }`}
          >
            {showInjectForm ? '✕ Cancel' : '+ Inject Signal'}
          </button>
        ) : null}
      </div>

      {showInjectForm ? (
        <div className="rounded-lg border border-blue/30 bg-surface p-6 shadow-lg shadow-blue/5 transition-all">
          <div className="mb-1 font-mono text-[10px] uppercase tracking-[3px] text-muted">
            MANUAL SIGNAL INJECTION
          </div>
          <div className="mb-4 font-mono text-[10px] text-amber">
            Bypasses scanner. Risk Gatekeeper still applies.
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div>
              <label className={LABEL_CLASS}>Symbol</label>
              <input
                type="text"
                value={injectForm.symbol}
                onChange={(e) =>
                  setInjectForm((prev) => ({
                    ...prev,
                    symbol: e.target.value.toUpperCase()
                  }))
                }
                placeholder="e.g. NHPC"
                className={INPUT_CLASS}
              />
            </div>

            <div>
              <label className={LABEL_CLASS}>Action</label>
              <select
                value={injectForm.action}
                onChange={(e) =>
                  setInjectForm((prev) => ({ ...prev, action: e.target.value }))
                }
                className={INPUT_CLASS}
              >
                <option value="BUY">BUY</option>
                <option value="SELL">SELL</option>
              </select>
            </div>

            <div>
              <label className={LABEL_CLASS}>Entry Price (₹)</label>
              <input
                type="number"
                step="0.05"
                value={injectForm.entry_price}
                onChange={(e) =>
                  setInjectForm((prev) => ({
                    ...prev,
                    entry_price: e.target.value
                  }))
                }
                placeholder="e.g. 84.10"
                className={INPUT_CLASS}
              />
            </div>

            <div>
              <label className={LABEL_CLASS}>Target (₹)</label>
              <input
                type="number"
                step="0.05"
                value={injectForm.target}
                onChange={(e) =>
                  setInjectForm((prev) => ({ ...prev, target: e.target.value }))
                }
                placeholder="e.g. 89.50"
                className={INPUT_CLASS}
              />
              {upside ? (
                <div className="mt-1 font-mono text-[10px] text-green">
                  +{upside}% from entry
                </div>
              ) : null}
            </div>

            <div>
              <label className={LABEL_CLASS}>Stoploss (₹)</label>
              <input
                type="number"
                step="0.05"
                value={injectForm.stoploss}
                onChange={(e) =>
                  setInjectForm((prev) => ({
                    ...prev,
                    stoploss: e.target.value
                  }))
                }
                placeholder="e.g. 81.00"
                className={INPUT_CLASS}
              />
              {downside ? (
                <div className="mt-1 font-mono text-[10px] text-red">
                  -{downside}% from entry
                </div>
              ) : null}
            </div>

            <div>
              <label className={LABEL_CLASS}>Quantity</label>
              <input
                type="number"
                min="1"
                step="1"
                value={injectForm.qty}
                onChange={(e) =>
                  setInjectForm((prev) => ({ ...prev, qty: e.target.value }))
                }
                placeholder="e.g. 9"
                className={INPUT_CLASS}
              />
              {tradeValue ? (
                <div className="mt-1 font-mono text-[10px] text-muted">
                  Trade value: ₹{tradeValue}
                </div>
              ) : null}
            </div>
          </div>

          {injectError ? (
            <div className="mt-4 rounded border border-red/30 bg-red-dim p-3 font-mono text-[11px] text-red">
              {injectError}
            </div>
          ) : null}

          {injectSuccess ? (
            <div className="mt-4 rounded border border-green/30 bg-green-dim p-3 font-mono text-[11px] text-green">
              ✓ Signal injected successfully
            </div>
          ) : null}

          <button
            type="button"
            disabled={injecting}
            onClick={handleInject}
            className="mt-4 w-full rounded border border-blue/30 bg-blue-dim py-2.5 font-mono text-[11px] font-bold uppercase tracking-wider text-blue transition-colors hover:bg-blue/20 disabled:opacity-50"
          >
            {injecting ? 'Injecting...' : 'Inject Signal'}
          </button>
        </div>
      ) : null}

      <div>
        <div className="mb-3 flex items-center justify-between">
          <div className="font-mono text-[10px] uppercase tracking-[3px] text-muted">
            TODAY&apos;S SIGNALS
          </div>
          <div className="font-mono text-[11px] text-muted">
            {displayTodaySignals.length} signals
          </div>
        </div>

        {loading ? null : displayTodaySignals.length === 0 ? (
          <div className="rounded-lg border border-border bg-surface p-8 text-center">
            <div className="mb-3 text-3xl">📡</div>
            <div className="font-display font-bold text-text">
              No signals yet today
            </div>
            <div className="mt-2 font-mono text-sm text-muted">
              Trigger a scan or wait for scheduled scans
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {displayTodaySignals.map((signal) => (
              <div
                key={signal.id}
                className="cursor-pointer"
                onClick={() =>
                  setExpandedSignal((prev) => (prev === signal.id ? null : signal.id))
                }
              >
                <SignalChip signal={signal} />
                {expandedSignal === signal.id ? (
                  <div className="mt-2 fade-in">
                    <SignalDetail signal={signal} />
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </div>

      {analytics ? (
        <div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="TOTAL SIGNALS"
              value={`${analytics.total || 0}`}
              sub="all tracked signals"
              accent="blue"
              icon="📡"
            />
            <StatCard
              label="APPROVED"
              value={`${approvalRate}%`}
              sub={`${approvedCount} of ${analytics.total || 0}`}
              accent={Number(approvalRate) >= 50 ? 'green' : 'amber'}
              icon="✓"
            />
            <StatCard
              label="EXECUTED"
              value={`${analytics.executed || 0}`}
              sub="signals forwarded"
              accent="blue"
              icon="⚡"
            />
            <StatCard
              label="AVG CONFIDENCE"
              value={
                analytics.avg_confidence != null
                  ? `${Number(analytics.avg_confidence).toFixed(0)}%`
                  : '—'
              }
              sub="across evaluated signals"
              accent="amber"
              icon="🎯"
            />
          </div>

          {analytics.rejection_reasons?.length > 0 ? (
            <div className="mt-4 rounded-lg border border-border bg-surface p-5">
              <div className="mb-4 font-mono text-[10px] uppercase tracking-[3px] text-muted">
                REJECTION REASONS
              </div>

              {analytics.rejection_reasons.map((reason) => (
                <div
                  key={`${reason.reason}-${reason.count}`}
                  className="mb-3 flex items-center gap-3 last:mb-0"
                >
                  <div className="flex-1 font-mono text-[11px] text-muted">
                    {reason.reason}
                  </div>
                  <div className="flex-1 rounded-full bg-surface2">
                    <div
                      className="h-1.5 rounded-full bg-red"
                      style={{
                        width: `${(reason.count / maxRejectCount) * 100}%`
                      }}
                    />
                  </div>
                  <div className="font-mono text-[11px] font-semibold text-red">
                    {reason.count}
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      <div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="font-mono text-[10px] uppercase tracking-[3px] text-muted">
            ALL SIGNALS
          </div>
          <div className="flex gap-3">
            <select
              value={filter.mode}
              onChange={(e) =>
                setFilter((prev) => ({ ...prev, mode: e.target.value }))
              }
              className="rounded border border-border bg-surface2 px-2 py-1.5 font-mono text-[10px] text-muted"
            >
              <option value="all">All</option>
              <option value="paper">Paper</option>
              <option value="live">Live</option>
            </select>

            <select
              value={filter.status}
              onChange={(e) =>
                setFilter((prev) => ({ ...prev, status: e.target.value }))
              }
              className="rounded border border-border bg-surface2 px-2 py-1.5 font-mono text-[10px] text-muted"
            >
              <option value="all">All</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="pending">Pending</option>
            </select>
          </div>
        </div>

        <div className="mt-3 overflow-hidden rounded-lg border border-border bg-surface">
          {allSignals.length === 0 ? (
            <div className="p-8 text-center font-mono text-sm text-muted">
              No signals found
            </div>
          ) : (
            <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted">Time</th>
                  <th className="px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted">Symbol</th>
                  <th className="px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted">Action</th>
                  <th className="hidden px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted md:table-cell">Entry</th>
                  <th className="hidden px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted md:table-cell">Target</th>
                  <th className="hidden px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted md:table-cell">SL</th>
                  <th className="hidden px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted md:table-cell">RSI</th>
                  <th className="hidden px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted md:table-cell">MACD</th>
                  <th className="px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted">Conf</th>
                  <th className="px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted">Status</th>
                  <th className="hidden px-4 py-3 text-left font-mono text-[9px] font-normal uppercase tracking-[2px] text-muted sm:table-cell">Mode</th>
                </tr>
              </thead>
              <tbody>
                {allSignals.map((signal) => {
                  const rsiValue = Number(signal?.rsi)
                  const confidence = Number(signal?.confidence || 0)
                  return (
                    <tr
                      key={signal.id}
                      className="border-b border-border font-mono text-[11px] transition-colors hover:bg-surface2 last:border-0"
                      title={signal.reject_reason || ''}
                    >
                      <td className="px-4 py-3 text-muted">
                        {signal.timestamp}
                      </td>
                      <td className="px-4 py-3 font-semibold text-text">
                        {signal.symbol}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded px-1.5 py-0.5 text-[9px] ${
                            signal.action === 'SELL'
                              ? 'bg-red-dim text-red'
                              : 'bg-green-dim text-green'
                          }`}
                        >
                          {signal.action}
                        </span>
                      </td>
                      <td className="hidden px-4 py-3 text-text md:table-cell">
                        ₹{Number(signal.entry_price).toFixed(2)}
                      </td>
                      <td className="hidden px-4 py-3 text-green md:table-cell">
                        ₹{Number(signal.target).toFixed(2)}
                      </td>
                      <td className="hidden px-4 py-3 text-red md:table-cell">
                        ₹{Number(signal.stoploss).toFixed(2)}
                      </td>
                      <td
                        className={`hidden px-4 py-3 md:table-cell ${
                          rsiValue < 35
                            ? 'text-green'
                            : rsiValue > 65
                              ? 'text-red'
                              : 'text-text'
                        }`}
                      >
                        {signal.rsi != null ? Number(signal.rsi).toFixed(1) : '—'}
                      </td>
                      <td className={`hidden px-4 py-3 md:table-cell ${macdClass(signal.macd_state)}`}>
                        {macdLabel(signal)}
                      </td>
                      <td
                        className={`px-4 py-3 ${
                          confidence >= 75
                            ? 'text-green'
                            : confidence >= 60
                              ? 'text-amber'
                              : 'text-red'
                        }`}
                      >
                        {confidence}%
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider ${statusBadgeClass(
                            signal.risk_status || 'pending'
                          )}`}
                        >
                          {signal.risk_status || 'pending'}
                        </span>
                        {signal.risk_status === 'rejected' &&
                        signal.reject_reason ? (
                          <div className="mt-1 max-w-48 text-[10px] text-red">
                            {signal.reject_reason}
                          </div>
                        ) : null}
                      </td>
                      <td className="hidden px-4 py-3 sm:table-cell">
                        <span
                          className={`rounded border px-2 py-0.5 text-[9px] uppercase tracking-wider ${
                            signal.mode === 'live'
                              ? 'border-green/30 bg-green-dim text-green'
                              : 'border-amber/30 bg-amber-dim text-amber'
                          }`}
                        >
                          {signal.mode}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
