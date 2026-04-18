import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' }
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      'Request failed'

    console.error('[API]', message, error)
    error.message = message
    return Promise.reject(error)
  }
)

export const getStatus = () => client.get('/status')
export const getConfig = () => client.get('/config')
export const updateConfig = (data) => client.post('/config', data)

export const getAgents = () => client.get('/agents')
export const startAgent = (name) => client.post(`/agents/${name}/start`)
export const stopAgent = (name) => client.post(`/agents/${name}/stop`)
export const restartAgent = (name) => client.post(`/agents/${name}/restart`)
export const triggerScan = () => client.post('/agents/scanner/trigger')
export const getAgentLogs = (params) => client.get('/agents/logs', { params })

export const getPositions = () => client.get('/positions')
export const closePosition = (id) => client.post(`/positions/${id}/close`)
export const getMargin = () => client.get('/margin')

export const getTrades = (params) => client.get('/trades', { params })
export const getTradeStats = () => client.get('/trades/stats')
export const getTradeById = (id) => client.get(`/trades/${id}`)

export const getSignals = (params) => client.get('/signals', { params })
export const getTodaySignals = () => client.get('/signals/today')
export const injectSignal = (data) => client.post('/signals/manual', data)
export const getSignalAnalytics = () => client.get('/signals/analytics')

export default client
