import { create } from 'zustand'

const useStore = create((set, get) => ({
  // ── System ──────────────────────────────
  mode: 'paper',
  wsConnected: false,
  setMode: (mode) => set({ mode }),
  setWsConnected: (v) => set({ wsConnected: v }),

  // ── Capital ─────────────────────────────
  capital: {
    total: 5000,
    available: 3241.5,
    deployed: 1758.5,
    today_pnl: 0,
    today_pnl_pct: 0,
    open_positions: 0,
    trades_today: 0
  },
  setCapital: (data) => set({ capital: { ...get().capital, ...data } }),
  updatePnl: (total_pnl, total_pnl_pct, available_capital) =>
    set((state) => ({
      capital: {
        ...state.capital,
        today_pnl: total_pnl,
        today_pnl_pct: total_pnl_pct,
        available: available_capital,
        deployed: state.capital.total - available_capital
      }
    })),

  // ── Agents ──────────────────────────────
  agents: {
    market_scanner: { status: 'stopped', last_run: null, mode: 'paper' },
    risk_gatekeeper: { status: 'running', last_run: null, mode: 'paper' },
    execution: { status: 'stopped', last_run: null, mode: 'paper' }
  },
  setAgentStatus: (name, status) =>
    set((state) => ({
      agents: {
        ...state.agents,
        [name]: { ...state.agents[name], status }
      }
    })),
  updateAgentLastRun: (name, last_run) =>
    set((state) => ({
      agents: {
        ...state.agents,
        [name]: { ...state.agents[name], last_run }
      }
    })),

  // ── Positions ───────────────────────────
  positions: [],
  setPositions: (positions) => set({ positions }),
  updateLtp: (symbol, ltp) =>
    set((state) => ({
      positions: state.positions.map((p) => {
        if (p.symbol !== symbol) return p
        const action = p.action || 'BUY'
        let pnl, pnl_pct
        if (action === 'BUY') {
          pnl = (ltp - p.entry_price) * p.qty
          pnl_pct = ((ltp - p.entry_price) / p.entry_price) * 100
        } else {
          pnl = (p.entry_price - ltp) * p.qty
          pnl_pct = ((p.entry_price - ltp) / p.entry_price) * 100
        }
        return {
          ...p,
          ltp,
          pnl: parseFloat(pnl.toFixed(2)),
          pnl_pct: parseFloat(pnl_pct.toFixed(2))
        }
      })
    })),

  // ── Trades ──────────────────────────────
  trades: [],
  tradeStats: {},
  setTrades: (trades) => set({ trades }),
  setTradeStats: (tradeStats) => set({ tradeStats }),

  // ── Signals ─────────────────────────────
  signals: [],
  setSignals: (signals) => set({ signals }),
  addSignal: (signal) =>
    set((state) => ({ signals: [signal, ...state.signals] })),

  // ── Logs ────────────────────────────────
  // Max 500 entries, newest first, FIFO drop oldest
  logs: [],
  logFilter: { agent: 'all', level: 'all' },
  addLog: (log) =>
    set((state) => {
      const updated = [log, ...state.logs]
      return { logs: updated.slice(0, 500) }
    }),
  clearLogs: () => set({ logs: [] }),
  setLogFilter: (filter) =>
    set((state) => ({ logFilter: { ...state.logFilter, ...filter } })),

  // ── Config ──────────────────────────────
  config: null,
  setConfig: (config) => set({ config })
}))

export default useStore
