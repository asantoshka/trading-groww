import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'

import useStore from '../store/useStore'

const NAV = [
  { path: '/', icon: '📊', label: 'Dashboard' },
  { path: '/positions', icon: '📈', label: 'Live Positions' },
  { path: '/agents', icon: '🤖', label: 'Agent Control' },
  { path: '/history', icon: '📋', label: 'Trade History' },
  { path: '/signals', icon: '📡', label: 'Signals' },
  { path: '/paper', icon: '🧪', label: 'Paper Trading' }
]

export default function Sidebar({ open = false, onClose }) {
  const mode = useStore((s) => s.mode)
  const wsConnected = useStore((s) => s.wsConnected)
  const [time, setTime] = useState(
    new Date().toLocaleTimeString('en-IN', {
      timeZone: 'Asia/Kolkata',
      hour12: false
    })
  )

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(
        new Date().toLocaleTimeString('en-IN', {
          timeZone: 'Asia/Kolkata',
          hour12: false
        })
      )
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  return (
    <>
      <div
        className={`fixed inset-0 z-50 bg-black/60 transition-opacity duration-200 md:hidden ${
          open ? 'pointer-events-auto opacity-100' : 'pointer-events-none opacity-0'
        }`}
        onClick={onClose}
      />

      <aside
        className={`fixed left-0 top-0 z-50 flex h-full w-[220px] flex-col border-r border-border bg-surface transition-transform duration-200 md:z-40 md:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-[56px] items-center justify-between border-b border-border px-4">
          <div className="flex min-w-0 items-center">
            <div className="mr-3 h-3 w-3 bg-green" />
            <div>
              <div className="font-display text-sm font-bold text-text">
                GROWW BOT
              </div>
              <div className="text-xs text-muted">₹5,000 Capital</div>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded border border-border px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-muted transition-colors hover:border-border-hover hover:text-text md:hidden"
          >
            Close
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto py-4">
          {NAV.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              onClick={onClose}
              className={({ isActive }) =>
                [
                  'flex items-center gap-3 border-l-2 px-4 py-2.5 text-sm font-mono transition-colors duration-150',
                  isActive
                    ? 'border-green bg-green-dim text-green'
                    : 'border-transparent text-muted hover:bg-surface2 hover:text-text'
                ].join(' ')
              }
            >
              <span className="text-base" aria-hidden="true">
                {item.icon}
              </span>
              <span className="text-sm">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-border p-4">
          <div className="mb-3">
            {mode === 'paper' ? (
              <span className="rounded-full border border-amber/30 bg-amber-dim px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-amber">
                ● PAPER MODE
              </span>
            ) : (
              <span className="rounded-full border border-green/30 bg-green-dim px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-green">
                ● LIVE MODE
              </span>
            )}
          </div>

          <div className="mb-2 hidden text-[11px] text-muted md:block">{time}</div>

          <div
            className={`text-[10px] ${wsConnected ? 'text-green' : 'text-red'}`}
          >
            ● {wsConnected ? 'Connected' : 'Disconnected'}
          </div>
        </div>
      </aside>
    </>
  )
}
