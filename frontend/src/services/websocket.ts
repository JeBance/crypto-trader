/** WebSocket service for realtime updates */

export type WSMessageType = 'connected' | 'order' | 'position' | 'signal' | 'price' | 'pong' | 'subscribed' | 'unsubscribed'

export interface WSMessage {
  type: WSMessageType
  data?: Record<string, unknown>
  client_id?: string
  channel?: string
  timestamp?: string
}

export type WSEventHandler = (message: WSMessage) => void

export interface WebSocketService {
  connect: (options?: { channels?: string[]; onMessage?: WSEventHandler }) => void
  disconnect: () => void
  subscribe: (channel: string) => void
  unsubscribe: (channel: string) => void
  send: (data: Record<string, unknown>) => void
  isConnected: () => boolean
}

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

class WebSocketServiceImpl implements WebSocketService {
  private ws: WebSocket | null = null
  private reconnectTimer: number | null = null
  private eventHandlers: Set<WSEventHandler> = new Set()
  private clientId: string = `client_${Date.now()}`
  private shouldReconnect = true

  connect(options: { channels?: string[]; onMessage?: WSEventHandler } = {}): void {
    const { channels = [], onMessage } = options
    
    if (onMessage) {
      this.eventHandlers.add(onMessage)
    }

    const channelsParam = channels.length > 0 ? `&channels=${channels.join(',')}` : ''
    const url = `${WS_URL}/ws/stream?client_id=${this.clientId}${channelsParam}`
    
    console.log('[WS] Connecting to:', url)
    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      console.log('[WS] Connected')
      this.shouldReconnect = true
    }

    this.ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data)
        console.log('[WS] Message received:', message)
        this.eventHandlers.forEach(handler => handler(message))
      } catch (error) {
        console.error('[WS] Error parsing message:', error)
      }
    }

    this.ws.onclose = () => {
      console.log('[WS] Disconnected')
      if (this.shouldReconnect) {
        this.scheduleReconnect()
      }
    }

    this.ws.onerror = (error) => {
      console.error('[WS] Error:', error)
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }
    
    console.log('[WS] Scheduling reconnect in 5 seconds...')
    this.reconnectTimer = window.setTimeout(() => {
      this.connect({ channels: [] })
    }, 5000)
  }

  disconnect(): void {
    this.shouldReconnect = false
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    console.log('[WS] Disconnected by user')
  }

  subscribe(channel: string): void {
    this.send({ action: 'subscribe', channel })
  }

  unsubscribe(channel: string): void {
    this.send({ action: 'unsubscribe', channel })
  }

  send(data: Record<string, unknown>): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('[WS] Cannot send - not connected')
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }

  addHandler(handler: WSEventHandler): void {
    this.eventHandlers.add(handler)
  }

  removeHandler(handler: WSEventHandler): void {
    this.eventHandlers.delete(handler)
  }
}

// Singleton instance
export const wsService: WebSocketService = new WebSocketServiceImpl()

export default wsService
