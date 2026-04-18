import { useLocation } from 'react-router-dom'

import useStore from '../store/useStore'

const TITLES = {
  '/': 'Dashboard',
  '/positions': 'Live Positions',
  '/agents': 'Agent Control',
  '/history': 'Trade History',
  '/signals': 'Signals',
  '/paper': 'Paper Trading'
}

export default function TopBar({ onMenuClick }) {
  const location = useLocation()
  const capital = useStore((s) => s.capital)
  const agents = useStore((s) => s.agents)
  const runningCount = Object.values(agents).filter(
    (agent) => agent.status === 'running'
  ).length

  return (
    <header className="fixed left-0 right-0 top-0 z-20 flex h-[56px] min-w-0 items-center justify-between border-b border-border bg-surface px-4 sm:px-5 md:left-[220px] lg:px-6">
      <div className="flex min-w-0 items-center gap-3 pr-3">
        <button
          type="button"
          onClick={onMenuClick}
          className="flex h-9 w-9 items-center justify-center rounded border border-border text-muted transition-colors hover:border-border-hover hover:text-text md:hidden"
          aria-label="Open navigation menu"
        >
          <span className="text-lg leading-none">☰</span>
        </button>
        <div className="truncate font-display text-sm font-bold text-text sm:text-base">
          {TITLES[location.pathname] || 'Groww Agent Trading'}
        </div>
      </div>

      <div className="hidden min-w-0 items-center gap-4 overflow-hidden md:flex">
        <div className="truncate font-mono text-[11px] text-muted">
          Available: ₹{capital.available.toFixed(2)}
          <span className="mx-2 text-muted2">|</span>
          Deployed: ₹{capital.deployed.toFixed(2)}
        </div>

        <div
          className={`shrink-0 font-mono text-[12px] font-semibold ${
            capital.today_pnl >= 0 ? 'text-green' : 'text-red'
          }`}
        >
          {capital.today_pnl >= 0
            ? `+₹${capital.today_pnl.toFixed(2)} (+${capital.today_pnl_pct.toFixed(2)}%)`
            : `₹${capital.today_pnl.toFixed(2)} (${capital.today_pnl_pct.toFixed(2)}%)`}
        </div>

        {runningCount > 0 ? (
          <div className="flex shrink-0 items-center gap-2 text-[11px] text-green">
            <span className="pulse inline-block h-2 w-2 rounded-full bg-green" />
            <span>{runningCount} running</span>
          </div>
        ) : null}
      </div>

      <div className="hidden shrink-0 items-center rounded border border-green/30 bg-green/10 px-2 py-0.5 font-mono text-[10px] text-green md:flex">
        v1.0 · CI/CD ✓
      </div>

      <div className="flex items-center gap-3 md:hidden">
        <div
          className={`font-mono text-[10px] font-semibold ${
            capital.today_pnl >= 0 ? 'text-green' : 'text-red'
          }`}
        >
          {capital.today_pnl >= 0 ? '+' : ''}
          ₹{capital.today_pnl.toFixed(0)}
        </div>
      </div>
    </header>
  )
}
