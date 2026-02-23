/** API configuration and types */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface Order {
  id: number
  exchange_order_id: string
  symbol: string
  side: 'buy' | 'sell'
  type: 'market' | 'limit'
  quantity: number
  price: number | null
  filled_quantity: number
  average_price: number
  status: 'pending' | 'open' | 'filled' | 'cancelled' | 'rejected'
  strategy_name: string | null
  created_at: string
  updated_at: string
}

export interface Position {
  id: number
  symbol: string
  side: 'long' | 'short'
  quantity: number
  entry_price: number
  current_price: number
  unrealized_pnl: number
  realized_pnl: number
  pnl_percent: number
  stop_loss: number | null
  take_profit: number | null
  opened_at: string
  closed_at: string | null
}

export interface Strategy {
  name: string
  version: string
  description: string
  initialized: boolean
  active: boolean
  parameters: Record<string, unknown>
  symbols?: string[]
  timeframe?: string
}

export interface Candle {
  symbol: string
  timeframe: string
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface Ticker {
  symbol: string
  last_price: number
  bid: number
  ask: number
  high_24h: number
  low_24h: number
  volume_24h: number
  change_24h: number
  change_percent_24h: number
}

export interface HealthStatus {
  status: string
  name: string
  version: string
  timestamp: string
}

export interface ServerStatus {
  status: string
  uptime_seconds: number | null
  last_restart: string | null
  last_update: string | null
  restart_pending: boolean
  update_pending: boolean
  version: string
}

export interface Config {
  app: {
    env: string
    debug: boolean
    log_level: string
  }
  server: {
    host: string
    port: number
  }
  trading: {
    mode: string
    max_position_size_percent: number
    stop_loss_percent: number
    take_profit_percent: number
    daily_loss_limit_percent: number
  }
  exchanges: {
    binance: {
      configured: boolean
      testnet: boolean
    }
    bybit: {
      configured: boolean
      testnet: boolean
    }
  }
  notifications: {
    telegram: {
      configured: boolean
    }
  }
}

/** API Client */

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export const api = {
  // Health
  async getHealth(): Promise<HealthStatus> {
    const response = await fetch(`${API_BASE_URL}/api/health`)
    return handleResponse<HealthStatus>(response)
  },

  async getHealthStatus(): Promise<Record<string, unknown>> {
    const response = await fetch(`${API_BASE_URL}/api/health/status`)
    return handleResponse<Record<string, unknown>>(response)
  },

  // Config
  async getConfig(): Promise<Config> {
    const response = await fetch(`${API_BASE_URL}/api/config`)
    return handleResponse<Config>(response)
  },

  // Orders
  async getOrders(params?: { status?: string; symbol?: string; limit?: number }): Promise<{ orders: Order[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.set('status', params.status)
    if (params?.symbol) searchParams.set('symbol', params.symbol)
    if (params?.limit) searchParams.set('limit', String(params.limit))
    
    const response = await fetch(`${API_BASE_URL}/api/orders?${searchParams}`)
    return handleResponse(response)
  },

  async getOrder(orderId: string): Promise<Order> {
    const response = await fetch(`${API_BASE_URL}/api/orders/${orderId}`)
    return handleResponse<Order>(response)
  },

  async createOrder(data: {
    symbol: string
    side: string
    type: string
    quantity: number
    price?: number
    strategy_name?: string
  }): Promise<Record<string, unknown>> {
    const response = await fetch(`${API_BASE_URL}/api/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return handleResponse(response)
  },

  async cancelOrder(orderId: string): Promise<Record<string, unknown>> {
    const response = await fetch(`${API_BASE_URL}/api/orders/${orderId}`, {
      method: 'DELETE',
    })
    return handleResponse(response)
  },

  // Positions
  async getPositions(includeClosed = false): Promise<{ positions: Position[]; total: number }> {
    const response = await fetch(`${API_BASE_URL}/api/positions?include_closed=${includeClosed}`)
    return handleResponse(response)
  },

  async getPosition(symbol: string): Promise<Position> {
    const response = await fetch(`${API_BASE_URL}/api/positions/${symbol}`)
    return handleResponse<Position>(response)
  },

  async closePosition(symbol: string): Promise<Record<string, unknown>> {
    const response = await fetch(`${API_BASE_URL}/api/positions/${symbol}/close`, {
      method: 'POST',
    })
    return handleResponse(response)
  },

  // Strategies
  async getStrategies(): Promise<{ strategies: Strategy[]; total: number }> {
    const response = await fetch(`${API_BASE_URL}/api/strategies`)
    return handleResponse(response)
  },

  async getStrategy(name: string): Promise<Strategy> {
    const response = await fetch(`${API_BASE_URL}/api/strategies/${name}`)
    return handleResponse<Strategy>(response)
  },

  async activateStrategy(name: string, config?: { enabled?: boolean; parameters?: Record<string, unknown> }): Promise<Record<string, unknown>> {
    const response = await fetch(`${API_BASE_URL}/api/strategies/${name}/activate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config || {}),
    })
    return handleResponse(response)
  },

  async deactivateStrategy(name: string): Promise<Record<string, unknown>> {
    const response = await fetch(`${API_BASE_URL}/api/strategies/${name}/deactivate`, {
      method: 'POST',
    })
    return handleResponse(response)
  },

  // Server Management
  async getServerStatus(): Promise<ServerStatus> {
    const response = await fetch(`${API_BASE_URL}/api/server/status`)
    return handleResponse<ServerStatus>(response)
  },

  async restartServer(): Promise<Record<string, unknown>> {
    const response = await fetch(`${API_BASE_URL}/api/server/restart`, {
      method: 'POST',
    })
    return handleResponse(response)
  },

  async updateServer(): Promise<Record<string, unknown>> {
    const response = await fetch(`${API_BASE_URL}/api/server/update`, {
      method: 'POST',
    })
    return handleResponse(response)
  },

  async getServerLogs(lines = 50): Promise<{ logs: string[]; count: number }> {
    const response = await fetch(`${API_BASE_URL}/api/server/logs?lines=${lines}`)
    return handleResponse(response)
  },

  async updateStrategyParameters(name: string, parameters: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await fetch(`${API_BASE_URL}/api/strategies/${name}/parameters`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(parameters),
    })
    return handleResponse(response)
  },
}

export default api
