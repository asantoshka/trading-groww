import { useCallback, useEffect, useMemo, useState } from 'react'

import {
  getAgentLogs,
  getAgents,
  getConfig,
  restartAgent,
  startAgent,
  stopAgent,
  triggerScan,
  updateConfig
} from '../api/client'
import AgentCard from '../components/AgentCard'
import ConfigPanel from '../components/ConfigPanel'
import LogStream from '../components/LogStream'
import ModeToggle from '../components/ModeToggle'
import useStore from '../store/useStore'

const AGENT_KEYS = ['market_scanner', 'risk_gatekeeper', 'execution']

export default function AgentControl() {
  const [agents, setAgents] = useState({})
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [savingConfig, setSavingConfig] = useState(false)
  const [triggering, setTriggering] = useState(false)
  const [triggerSuccess, setTriggerSuccess] = useState(false)

  const storeAgents = useStore((s) => s.agents)
  const logs = useStore((s) => s.logs)
  const addLog = useStore((s) => s.addLog)
  const mode = useStore((s) => s.mode)
  const setMode = useStore((s) => s.setMode)

  const loadAgents = useCallback(async () => {
    const response = await getAgents()
    setAgents(response.data || {})
  }, [])

  const loadConfig = useCallback(async () => {
    const response = await getConfig()
    setConfig(response.data || null)
  }, [])

  useEffect(() => {
    let mounted = true

    async function loadPage() {
      setLoading(true)
      try {
        const [agentsRes, configRes, logsRes] = await Promise.all([
          getAgents(),
          getConfig(),
          getAgentLogs({ limit: 100 })
        ])

        if (!mounted) return

        setAgents(agentsRes.data || {})
        setConfig(configRes.data || null)

        ;(logsRes.data?.logs || []).forEach((log) => addLog(log))
      } catch (error) {
        console.error(error)
      } finally {
        if (mounted) setLoading(false)
      }
    }

    loadPage()
    return () => {
      mounted = false
    }
  }, [addLog])

  const displayAgents = useMemo(
    () => ({
      market_scanner: {
        ...agents.market_scanner,
        ...storeAgents.market_scanner
      },
      risk_gatekeeper: {
        ...agents.risk_gatekeeper,
        ...storeAgents.risk_gatekeeper
      },
      execution: {
        ...agents.execution,
        ...storeAgents.execution
      }
    }),
    [agents, storeAgents]
  )

  const updateAgentState = (name, updates) => {
    setAgents((prev) => ({
      ...prev,
      [name]: {
        ...(prev[name] || {}),
        ...updates
      }
    }))
  }

  const handleStart = async (name) => {
    try {
      await startAgent(name)
      updateAgentState(name, { status: 'running' })
    } catch (error) {
      console.error(error)
    }
  }

  const handleStop = async (name) => {
    try {
      await stopAgent(name)
      updateAgentState(name, { status: 'stopped' })
    } catch (error) {
      console.error(error)
    }
  }

  const handleRestart = async (name) => {
    try {
      await restartAgent(name)
      updateAgentState(name, { status: 'running' })
    } catch (error) {
      console.error(error)
    }
  }

  const handleTriggerScan = async () => {
    setTriggering(true)
    try {
      await triggerScan()
      setTriggerSuccess(true)
      setTimeout(() => setTriggerSuccess(false), 3000)
      await loadAgents()
    } catch (error) {
      console.error(error)
    } finally {
      setTriggering(false)
    }
  }

  const handleSaveConfig = async (updatedConfig) => {
    setSavingConfig(true)
    try {
      const response = await updateConfig(updatedConfig)
      const nextConfig = response.data?.config || updatedConfig
      setConfig(nextConfig)
      setMode(nextConfig.mode)
    } catch (error) {
      console.error(error)
    } finally {
      setSavingConfig(false)
    }
  }

  const handleModeChange = async (newMode) => {
    const response = await updateConfig({ mode: newMode })
    const nextConfig = response.data?.config
      ? { ...config, ...response.data.config }
      : { ...config, mode: newMode }

    setMode(newMode)
    setConfig(nextConfig)
    setAgents((prev) => {
      const next = { ...prev }
      AGENT_KEYS.forEach((key) => {
        next[key] = { ...(next[key] || {}), mode: newMode }
      })
      return next
    })
  }

  const downloadLogs = () => {
    const content = logs
      .map(
        (log) =>
          `[${log.time}] [${log.agent.toUpperCase()}] [${log.level.toUpperCase()}] ${log.msg}`
      )
      .join('\n')

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    const date = new Date().toISOString().slice(0, 10)
    link.href = url
    link.download = `agent-logs-${date}.txt`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="fade-in space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-xl font-bold text-text">Agent Control</h1>
          <p className="mt-0.5 font-mono text-xs text-muted">
            Manage and configure trading agents
          </p>
        </div>

        <div className="flex w-full flex-col items-stretch gap-3 sm:w-auto sm:flex-row sm:flex-wrap sm:items-center sm:gap-4">
          <ModeToggle
            mode={config?.mode || mode || 'paper'}
            onModeChange={handleModeChange}
            disabled={loading}
          />

          <button
            type="button"
            onClick={handleTriggerScan}
            disabled={
              triggering || displayAgents.market_scanner?.status === 'running'
            }
            className={`rounded border px-4 py-2 font-mono text-[11px] font-bold uppercase tracking-wider transition-all duration-200 ${
              triggerSuccess
                ? 'border-green/30 bg-green-dim text-green'
                : triggering
                  ? 'cursor-not-allowed border-border bg-surface2 text-muted opacity-50'
                  : 'border-blue/30 bg-blue-dim text-blue hover:bg-blue/20'
            }`}
          >
            {triggerSuccess
              ? '✓ Scan Triggered'
              : triggering
                ? 'Triggering...'
                : '▶ Trigger Scan'}
          </button>
        </div>
      </div>

      <div>
        <div className="mb-3 font-mono text-[10px] uppercase tracking-[3px] text-muted">
          AGENT STATUS
        </div>

        <div className="space-y-3">
          {AGENT_KEYS.map((key) => (
            <div key={key}>
              <div className="flex flex-col gap-2">
                <AgentCard
                  name={key}
                  status={displayAgents[key]?.status || 'stopped'}
                  last_run={displayAgents[key]?.last_run || null}
                  mode={displayAgents[key]?.mode || 'paper'}
                  onStart={() => handleStart(key)}
                  onStop={() => handleStop(key)}
                />

                <div className="flex flex-col gap-3 pl-2 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
                  <div className="font-mono text-[10px] text-muted">
                    {key === 'market_scanner'
                      ? `Scans at: ${
                          config?.scan_times?.join(', ') || '09:15, 11:00, 13:30'
                        } IST`
                      : key === 'risk_gatekeeper'
                        ? `Max trade: ₹${config?.max_trade_value ?? 2000} | Max loss: ₹${
                            config?.max_loss_per_trade ?? 300
                          } | Min R:R: ${config?.min_rr_ratio ?? 1.5}`
                        : `Mode: ${displayAgents[key]?.mode || 'paper'} | Active positions: ${
                            displayAgents[key]?.active_positions ?? 0
                          }`}
                  </div>

                  <button
                    type="button"
                    onClick={() => handleRestart(key)}
                    className="rounded border border-blue/30 bg-blue-dim px-3 py-1.5 font-mono text-[10px] font-bold uppercase tracking-wider text-blue transition-colors hover:bg-blue/20"
                  >
                    Restart
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="mb-4 font-mono text-[10px] uppercase tracking-[3px] text-muted">
            CONFIGURATION
          </div>

          {config === null ? (
            <div>
              <div className="mb-3 h-10 animate-pulse rounded bg-surface2" />
              <div className="mb-3 h-10 animate-pulse rounded bg-surface2" />
              <div className="h-10 animate-pulse rounded bg-surface2" />
            </div>
          ) : (
            <ConfigPanel
              config={config}
              onSave={handleSaveConfig}
              saving={savingConfig}
            />
          )}
        </div>

        <div className="lg:col-span-1">
          <div className="mb-3 font-mono text-[10px] uppercase tracking-[3px] text-muted">
            AGENT LOGS
          </div>

          <LogStream maxLines={100} showFilter={true} />

          <button
            type="button"
            onClick={downloadLogs}
            className="mt-2 inline-block font-mono text-[10px] uppercase tracking-wider text-muted transition-colors hover:text-text"
          >
            ↓ Download Logs
          </button>
        </div>
      </div>
    </div>
  )
}
