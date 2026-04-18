import { useEffect, useMemo, useRef } from 'react'

import useStore from '../store/useStore'

const LEVEL_COLORS = {
  info: 'text-blue',
  success: 'text-green',
  warning: 'text-amber',
  error: 'text-red'
}

const AGENT_LABELS = {
  market_scanner: '[SCANNER]',
  risk_gatekeeper: '[RISK]   ',
  execution: '[EXEC]   '
}

export default function LogStream({ maxLines = 50, showFilter = false }) {
  const logs = useStore((s) => s.logs)
  const logFilter = useStore((s) => s.logFilter)
  const setLogFilter = useStore((s) => s.setLogFilter)
  const scrollRef = useRef(null)

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      const agentMatch =
        logFilter.agent === 'all' || log.agent === logFilter.agent
      const levelMatch =
        logFilter.level === 'all' || log.level === logFilter.level
      return agentMatch && levelMatch
    })
  }, [logs, logFilter])

  const visibleLogs = useMemo(() => {
    return filteredLogs.slice(0, maxLines).reverse()
  }, [filteredLogs, maxLines])

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs, filteredLogs.length])

  return (
    <div>
      {showFilter ? (
        <div className="mb-3 flex flex-col gap-2 sm:flex-row">
          <select
            value={logFilter.agent}
            onChange={(e) => setLogFilter({ agent: e.target.value })}
            className="rounded border border-border bg-surface2 px-2 py-1 font-mono text-[11px] text-muted"
          >
            <option value="all">all</option>
            <option value="market_scanner">market_scanner</option>
            <option value="risk_gatekeeper">risk_gatekeeper</option>
            <option value="execution">execution</option>
          </select>

          <select
            value={logFilter.level}
            onChange={(e) => setLogFilter({ level: e.target.value })}
            className="rounded border border-border bg-surface2 px-2 py-1 font-mono text-[11px] text-muted"
          >
            <option value="all">all</option>
            <option value="info">info</option>
            <option value="success">success</option>
            <option value="warning">warning</option>
            <option value="error">error</option>
          </select>
        </div>
      ) : null}

      <div
        ref={scrollRef}
        className="h-64 overflow-y-auto rounded-lg border border-border bg-bg p-3 font-mono text-[11px]"
      >
        {visibleLogs.length === 0 ? (
          <div className="flex h-full items-center justify-center text-center text-[11px] text-muted">
            No logs yet. Start an agent or fire a simulation.
          </div>
        ) : (
          visibleLogs.map((log, index) => {
            const levelClass = LEVEL_COLORS[log.level] || 'text-muted'
            const agentLabel = AGENT_LABELS[log.agent] || '[UNKNOWN]'
            return (
              <div
                key={`${log.time}-${log.agent}-${log.msg}-${log.timestamp || index}`}
                className="flex flex-col gap-1 py-1 hover:bg-surface/40 sm:flex-row sm:items-start sm:gap-2"
              >
                <div className="flex items-center gap-2 sm:w-32 sm:flex-shrink-0">
                  <div className="w-16 flex-shrink-0 text-muted">{log.time}</div>
                  <div className={`flex-shrink-0 sm:w-16 ${levelClass}`}>
                    {agentLabel}
                  </div>
                </div>
                <div className="flex-1 leading-relaxed text-text">
                  {log.msg}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
