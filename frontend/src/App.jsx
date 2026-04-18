import { useEffect } from 'react'
import { Route, Routes } from 'react-router-dom'

import { getConfig, getStatus } from './api/client'
import Layout from './components/Layout'
import useWebSocket from './hooks/useWebSocket'
import AgentControl from './pages/AgentControl'
import Dashboard from './pages/Dashboard'
import PaperTrading from './pages/PaperTrading'
import Positions from './pages/Positions'
import Signals from './pages/Signals'
import TradeHistory from './pages/TradeHistory'
import useStore from './store/useStore'

export default function App() {
  useWebSocket()
  const setCapital = useStore((s) => s.setCapital)
  const setConfig = useStore((s) => s.setConfig)
  const setMode = useStore((s) => s.setMode)

  useEffect(() => {
    getStatus()
      .then((res) => {
        if (res.data?.capital) setCapital(res.data.capital)
      })
      .catch(() => {})

    getConfig()
      .then((res) => {
        if (res.data) {
          setConfig(res.data)
          if (res.data.mode) setMode(res.data.mode)
        }
      })
      .catch(() => {})
  }, [setCapital, setConfig, setMode])

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="positions" element={<Positions />} />
        <Route path="agents" element={<AgentControl />} />
        <Route path="history" element={<TradeHistory />} />
        <Route path="signals" element={<Signals />} />
        <Route path="paper" element={<PaperTrading />} />
      </Route>
    </Routes>
  )
}
