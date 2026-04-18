import { useEffect, useRef } from 'react'

import {
  getAgentLogs,
  getStatus,
  getTodaySignals,
  startAgent,
  stopAgent
} from '../api/client'
import AgentCard from '../components/AgentCard'
import LogStream from '../components/LogStream'
import SignalChip from '../components/SignalChip'
import StatCard from '../components/StatCard'
import useStore from '../store/useStore'

const AGENT_ORDER = ['market_scanner', 'risk_gatekeeper', 'execution']

export default function Dashboard() {
  const didLoadRef = useRef(false)

  const capital = useStore((s) => s.capital)
  const agents = useStore((s) => s.agents)
  const signals = useStore((s) => s.signals)
  const setCapital = useStore((s) => s.setCapital)
  const setSignals = useStore((s) => s.setSignals)
  const addLog = useStore((s) => s.addLog)
  const clearLogs = useStore((s) => s.clearLogs)
  const setAgentStatus = useStore((s) => s.setAgentStatus)

  useEffect(() => {
    if (didLoadRef.current) return
    didLoadRef.current = true

    getStatus()
      .then((res) => {
        if (res.data?.capital) setCapital(res.data.capital)
        if (res.data?.agents) {
          Object.entries(res.data.agents).forEach(([name, agent]) => {
            setAgentStatus(name, agent.status)
            useStore.setState((state) => ({
              agents: {
                ...state.agents,
                [name]: {
                  ...state.agents[name],
                  ...agent
                }
              }
            }))
          })
        }
      })
      .catch(() => {})

    getTodaySignals()
      .then((res) => {
        if (Array.isArray(res.data?.signals)) {
          setSignals(res.data.signals)
        }
      })
      .catch(() => {})

    getAgentLogs({ limit: 50 })
      .then((res) => {
        if (!Array.isArray(res.data?.logs)) return

        const existingKeys = new Set(
          useStore
            .getState()
            .logs.map(
              (log) => `${log.time}|${log.agent}|${log.level}|${log.msg}`
            )
        )

        res.data.logs
          .slice()
          .reverse()
          .forEach((log) => {
            const key = `${log.time}|${log.agent}|${log.level}|${log.msg}`
            if (!existingKeys.has(key)) {
              addLog(log)
              existingKeys.add(key)
            }
          })
      })
      .catch(() => {})
  }, [addLog, setAgentStatus, setCapital, setSignals])

  const runningCount = Object.values(agents).filter(
    (agent) => agent.status === 'running'
  ).length

  const handleStart = async (name) => {
    try {
      await startAgent(name)
      setAgentStatus(name, 'running')
    } catch (error) {
      console.error(error)
    }
  }

  const handleStop = async (name) => {
    try {
      await stopAgent(name)
      setAgentStatus(name, 'stopped')
    } catch (error) {
      console.error(error)
    }
  }

  const deployedPct =
    capital.total > 0 ? (capital.deployed / capital.total) * 100 : 0
  const availablePct =
    capital.total > 0 ? (capital.available / capital.total) * 100 : 0

  return (
    <div className="fade-in space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <h1 className="font-display text-xl font-bold text-text">
            Dashboard
          </h1>
          <p className="mt-0.5 font-mono text-xs text-muted">
            Real-time system overview
          </p>
        </div>

        {runningCount > 0 ? (
          <div className="flex items-center gap-2">
            <span className="pulse h-2 w-2 rounded-full bg-green" />
            <span className="font-mono text-xs text-green">
              {runningCount} agent{runningCount > 1 ? 's' : ''} running
            </span>
          </div>
        ) : null}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="TOTAL CAPITAL"
          value={`₹${capital.total.toLocaleString('en-IN')}`}
          sub={`Available: ₹${capital.available.toFixed(2)}`}
          accent="blue"
          icon="💰"
        />
        <StatCard
          label="TODAY'S P&L"
          value={`${capital.today_pnl >= 0 ? '+' : ''}₹${capital.today_pnl.toFixed(2)}`}
          sub={`${capital.today_pnl >= 0 ? '+' : ''}${capital.today_pnl_pct.toFixed(2)}% return`}
          accent={capital.today_pnl >= 0 ? 'green' : 'red'}
          icon={capital.today_pnl >= 0 ? '📈' : '📉'}
        />
        <StatCard
          label="OPEN POSITIONS"
          value={`${capital.open_positions}`}
          sub={`${capital.trades_today} trades today`}
          accent="amber"
          icon="📋"
        />
        <StatCard
          label="AGENT HEALTH"
          value={`${runningCount}/3`}
          sub={runningCount > 0 ? 'System active' : 'All agents stopped'}
          accent={runningCount > 0 ? 'green' : 'red'}
          icon="🤖"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="mb-3 font-mono text-[10px] uppercase tracking-[3px] text-muted">
            AGENT STATUS
          </div>
          <div className="space-y-2">
            {AGENT_ORDER.map((key) => (
              <AgentCard
                key={key}
                name={key}
                status={agents[key]?.status}
                last_run={agents[key]?.last_run}
                mode={agents[key]?.mode}
                onStart={() => handleStart(key)}
                onStop={() => handleStop(key)}
              />
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-border bg-surface p-5">
          <div className="mb-3 font-mono text-[10px] uppercase tracking-[3px] text-muted">
            CAPITAL BREAKDOWN
          </div>

          <div>
            <div className="mb-1 flex justify-between text-xs">
              <span className="text-muted">Deployed</span>
              <span className="font-mono text-amber">
                ₹{capital.deployed.toFixed(0)}
              </span>
            </div>
            <div className="h-2 w-full rounded-full bg-surface2">
              <div
                className="h-full rounded-full bg-amber transition-all"
                style={{ width: `${deployedPct.toFixed(1)}%` }}
              />
            </div>
          </div>

          <div className="mt-4">
            <div className="mb-1 flex justify-between text-xs">
              <span className="text-muted">Available</span>
              <span className="font-mono text-green">
                ₹{capital.available.toFixed(0)}
              </span>
            </div>
            <div className="h-2 w-full rounded-full bg-surface2">
              <div
                className="h-full rounded-full bg-green transition-all"
                style={{ width: `${availablePct.toFixed(1)}%` }}
              />
            </div>
          </div>

          <div className="my-3 border-t border-border" />

          <div className="space-y-2">
            <div className="flex justify-between font-mono text-[11px]">
              <span className="text-muted">Total Capital</span>
              <span className="font-semibold text-text">
                ₹{capital.total.toLocaleString('en-IN')}
              </span>
            </div>
            <div className="flex justify-between font-mono text-[11px]">
              <span className="text-muted">Open Positions</span>
              <span className="font-semibold text-text">
                {capital.open_positions}
              </span>
            </div>
            <div className="flex justify-between font-mono text-[11px]">
              <span className="text-muted">Trades Today</span>
              <span className="font-semibold text-text">
                {capital.trades_today}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div>
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <div className="font-mono text-[10px] uppercase tracking-[3px] text-muted">
              RECENT SIGNALS
            </div>
          <div className="font-mono text-[11px] text-muted">
            {signals.length} today
          </div>
        </div>

        {signals.length === 0 ? (
          <div className="rounded-lg border border-border bg-surface p-6 text-center font-mono text-xs text-muted">
            No signals generated today. Agents are idle.
          </div>
        ) : (
          <div className="flex gap-3 overflow-x-auto pb-2">
            {signals.slice(0, 5).map((signal) => (
              <SignalChip key={signal.id} signal={signal} />
            ))}
          </div>
        )}
      </div>

      <div>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div className="font-mono text-[10px] uppercase tracking-[3px] text-muted">
            LIVE AGENT LOG
          </div>
          <button
            type="button"
            onClick={clearLogs}
            className="font-mono text-[10px] uppercase tracking-wider text-muted transition-colors hover:text-red"
          >
            CLEAR
          </button>
        </div>

        <LogStream maxLines={50} showFilter={true} />
      </div>
    </div>
  )
}
