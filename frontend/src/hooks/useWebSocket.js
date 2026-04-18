import { useEffect, useRef } from 'react'

import useStore from '../store/useStore'

export default function useWebSocket() {
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)
  const intentionalCloseRef = useRef(false)
  const store = useStore()

  function connect() {
    if (
      wsRef.current &&
      (wsRef.current.readyState === WebSocket.OPEN ||
        wsRef.current.readyState === WebSocket.CONNECTING)
    ) {
      return
    }

    intentionalCloseRef.current = false
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${protocol}://${window.location.host}/ws/feed`)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('[WS] Connected')
      store.setWsConnected(true)
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current)
        reconnectTimer.current = null
      }
    }

    ws.onmessage = (event) => {
      let msg
      try {
        msg = JSON.parse(event.data)
      } catch {
        return
      }

      switch (msg.type) {
        case 'ltp_update':
          store.updateLtp(msg.symbol, msg.ltp)
          break

        case 'agent_log':
          store.addLog({
            time: msg.time,
            agent: msg.agent,
            level: msg.level,
            msg: msg.msg,
            timestamp: msg.timestamp
          })
          break

        case 'new_signal':
          store.addSignal(msg.signal)
          break

        case 'pnl_update':
          store.updatePnl(
            msg.total_pnl,
            msg.total_pnl_pct,
            msg.available_capital
          )
          break

        case 'agent_status':
          store.setAgentStatus(msg.agent, msg.status)
          if (msg.last_run) {
            store.updateAgentLastRun(msg.agent, msg.last_run)
          }
          break

        case 'order_filled':
          store.addLog({
            time: new Date().toLocaleTimeString('en-IN', {
              timeZone: 'Asia/Kolkata',
              hour12: false
            }),
            agent: 'execution',
            level: 'success',
            msg: `Order filled: ${msg.action} ${msg.qty} ${msg.symbol} @ ₹${msg.price} [${msg.mode}]`,
            timestamp: msg.timestamp
          })
          break

        case 'connected':
          console.log('[WS] Server:', msg.message)
          break

        default:
          break
      }
    }

    ws.onclose = () => {
      store.setWsConnected(false)
      wsRef.current = null

      if (intentionalCloseRef.current) {
        intentionalCloseRef.current = false
        return
      }

      console.log('[WS] Disconnected. Reconnecting in 3s...')
      if (!reconnectTimer.current) {
        reconnectTimer.current = setTimeout(() => {
          reconnectTimer.current = null
          connect()
        }, 3000)
      }
    }

    ws.onerror = (err) => {
      if (intentionalCloseRef.current) return
      console.error('[WS] Error:', err)
      ws.close()
    }
  }

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      reconnectTimer.current = null
      intentionalCloseRef.current = true
      if (wsRef.current) wsRef.current.close()
    }
  }, [])

  function send(data) {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }

  return {
    connected: useStore((s) => s.wsConnected),
    send
  }
}
