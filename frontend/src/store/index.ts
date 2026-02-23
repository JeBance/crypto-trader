/** Redux store configuration */

import { configureStore, createSlice, PayloadAction } from '@reduxjs/toolkit'

// Types
interface Order {
  id: number
  exchange_order_id: string
  symbol: string
  side: string
  type: string
  quantity: number
  price: number | null
  filled_quantity: number
  average_price: number
  status: string
  strategy_name: string | null
  created_at: string
}

interface Position {
  id: number
  symbol: string
  side: string
  quantity: number
  entry_price: number
  current_price: number
  unrealized_pnl: number
  realized_pnl: number
  pnl_percent: number
}

interface Strategy {
  name: string
  version: string
  description: string
  initialized: boolean
  active: boolean
  parameters: Record<string, unknown>
}

interface AppState {
  orders: Order[]
  positions: Position[]
  strategies: Strategy[]
  config: Record<string, unknown> | null
  health: Record<string, unknown> | null
  loading: boolean
  error: string | null
  wsConnected: boolean
}

// Initial state
const initialState: AppState = {
  orders: [],
  positions: [],
  strategies: [],
  config: null,
  health: null,
  loading: false,
  error: null,
  wsConnected: false,
}

// Slice
const appSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    // Orders
    setOrders(state, action: PayloadAction<Order[]>) {
      state.orders = action.payload
    },
    addOrder(state, action: PayloadAction<Order>) {
      state.orders.unshift(action.payload)
    },
    updateOrder(state, action: PayloadAction<Order>) {
      const index = state.orders.findIndex(o => o.exchange_order_id === action.payload.exchange_order_id)
      if (index !== -1) {
        state.orders[index] = action.payload
      }
    },

    // Positions
    setPositions(state, action: PayloadAction<Position[]>) {
      state.positions = action.payload
    },
    addPosition(state, action: PayloadAction<Position>) {
      const index = state.positions.findIndex(p => p.symbol === action.payload.symbol)
      if (index !== -1) {
        state.positions[index] = action.payload
      } else {
        state.positions.push(action.payload)
      }
    },
    updatePosition(state, action: PayloadAction<Position>) {
      const index = state.positions.findIndex(p => p.symbol === action.payload.symbol)
      if (index !== -1) {
        state.positions[index] = action.payload
      }
    },
    removePosition(state, action: PayloadAction<string>) {
      state.positions = state.positions.filter(p => p.symbol !== action.payload)
    },

    // Strategies
    setStrategies(state, action: PayloadAction<Strategy[]>) {
      state.strategies = action.payload
    },
    updateStrategy(state, action: PayloadAction<{ name: string; updates: Partial<Strategy> }>) {
      const index = state.strategies.findIndex(s => s.name === action.payload.name)
      if (index !== -1) {
        state.strategies[index] = { ...state.strategies[index], ...action.payload.updates }
      }
    },

    // Config & Health
    setConfig(state, action: PayloadAction<Record<string, unknown>>) {
      state.config = action.payload
    },
    setHealth(state, action: PayloadAction<Record<string, unknown>>) {
      state.health = action.payload
    },

    // Loading & Error
    setLoading(state, action: PayloadAction<boolean>) {
      state.loading = action.payload
    },
    setError(state, action: PayloadAction<string | null>) {
      state.error = action.payload
    },

    // WebSocket
    setWsConnected(state, action: PayloadAction<boolean>) {
      state.wsConnected = action.payload
    },
  },
})

export const {
  setOrders,
  addOrder,
  updateOrder,
  setPositions,
  addPosition,
  updatePosition,
  removePosition,
  setStrategies,
  updateStrategy,
  setConfig,
  setHealth,
  setLoading,
  setError,
  setWsConnected,
} = appSlice.actions

// Store
export const store = configureStore({
  reducer: {
    app: appSlice.reducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

export default store
