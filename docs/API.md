# 📡 Crypto Trader API Documentation

Полная документация REST API и WebSocket endpoints.

**Base URL:** `http://localhost:8000`

**API Version:** 0.1.0

---

## 📑 Содержание

1. [REST API](#rest-api)
   - [Health](#health)
   - [Configuration](#configuration)
   - [Orders](#orders)
   - [Positions](#positions)
   - [Strategies](#strategies)
2. [WebSocket](#websocket)
3. [Models](#models)
4. [Error Handling](#error-handling)

---

## 🔧 REST API

### Health

#### GET `/api/health`

Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "name": "Crypto Trader",
  "version": "0.1.0",
  "timestamp": "2026-02-22T10:30:00.000000"
}
```

#### GET `/api/health/ready`

Readiness check endpoint.

**Response:**
```json
{
  "ready": true,
  "checks": {
    "config": true,
    "database": true,
    "exchanges": true
  }
}
```

#### GET `/api/health/status`

Detailed system status.

**Response:**
```json
{
  "application": {
    "name": "Crypto Trader",
    "version": "0.1.0",
    "environment": "development",
    "debug": true,
    "trading_mode": "paper"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000
  },
  "plugins": {
    "total": 3,
    "exchanges": {
      "binance": {
        "name": "binance",
        "version": "1.0.0",
        "description": "Binance cryptocurrency exchange",
        "initialized": "true"
      }
    },
    "strategies": {
      "rsi": {
        "name": "rsi",
        "version": "1.0.0",
        "description": "RSI overbought/oversold trading strategy",
        "initialized": "true"
      }
    },
    "notifiers": {
      "telegram": {
        "name": "telegram",
        "version": "1.0.0",
        "description": "Telegram bot notifications",
        "initialized": "true"
      }
    }
  }
}
```

---

### Configuration

#### GET `/api/config`

Get current application configuration (non-sensitive values only).

**Response:**
```json
{
  "app": {
    "env": "development",
    "debug": true,
    "log_level": "INFO"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000
  },
  "trading": {
    "mode": "paper",
    "max_position_size_percent": 10,
    "stop_loss_percent": 2,
    "take_profit_percent": 4,
    "daily_loss_limit_percent": 5
  },
  "exchanges": {
    "binance": {
      "configured": true,
      "testnet": true
    },
    "bybit": {
      "configured": false,
      "testnet": true
    }
  },
  "notifications": {
    "telegram": {
      "configured": true
    }
  }
}
```

#### GET `/api/config/env`

Get environment variables (sensitive values masked).

**Response:**
```json
{
  "variables": [
    {
      "key": "APP_ENV",
      "value": "development",
      "is_secret": false
    },
    {
      "key": "BINANCE_API_KEY",
      "value": "***configured***",
      "is_secret": true
    }
  ]
}
```

#### GET `/api/config/exchanges`

Get exchange configurations.

**Response:**
```json
{
  "binance": {
    "enabled": true,
    "testnet": true,
    "base_url": "https://testnet.binance.vision"
  },
  "bybit": {
    "enabled": false,
    "testnet": true,
    "base_url": "https://api-testnet.bybit.com"
  }
}
```

---

### Orders

#### GET `/api/orders`

Get all orders with optional filtering.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | - | Filter by status (pending, open, filled, cancelled) |
| `symbol` | string | - | Filter by symbol (e.g., BTCUSDT) |
| `limit` | integer | 50 | Number of orders (1-500) |

**Request:**
```
GET /api/orders?status=filled&symbol=BTCUSDT&limit=100
```

**Response:**
```json
{
  "orders": [
    {
      "id": 1,
      "exchange_order_id": "12345678901",
      "symbol": "BTCUSDT",
      "side": "buy",
      "type": "market",
      "quantity": 0.001,
      "price": null,
      "filled_quantity": 0.001,
      "average_price": 50000.0,
      "status": "filled",
      "strategy_name": "rsi",
      "created_at": "2026-02-22T10:30:00",
      "updated_at": "2026-02-22T10:30:05"
    }
  ],
  "total": 1
}
```

#### GET `/api/orders/{order_id}`

Get a specific order by ID.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `order_id` | string | Exchange order ID |

**Response:**
```json
{
  "id": 1,
  "exchange_order_id": "12345678901",
  "symbol": "BTCUSDT",
  "side": "buy",
  "type": "market",
  "quantity": 0.001,
  "price": null,
  "filled_quantity": 0.001,
  "average_price": 50000.0,
  "status": "filled",
  "strategy_name": "rsi",
  "created_at": "2026-02-22T10:30:00",
  "updated_at": "2026-02-22T10:30:05"
}
```

#### POST `/api/orders`

Create a new order.

**Request Body:**
```json
{
  "symbol": "BTCUSDT",
  "side": "buy",
  "type": "market",
  "quantity": 0.001,
  "strategy_name": "rsi"
}
```

**Response:**
```json
{
  "status": "pending",
  "message": "Order created successfully",
  "order": {
    "symbol": "BTCUSDT",
    "side": "buy",
    "type": "market",
    "quantity": 0.001
  }
}
```

#### DELETE `/api/orders/{order_id}`

Cancel an existing order.

**Response:**
```json
{
  "status": "success",
  "message": "Order cancelled",
  "order_id": "12345678901"
}
```

---

### Positions

#### GET `/api/positions`

Get all positions.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_closed` | boolean | false | Include closed positions |

**Response:**
```json
{
  "positions": [
    {
      "id": 1,
      "symbol": "BTCUSDT",
      "side": "long",
      "quantity": 0.001,
      "entry_price": 50000.0,
      "current_price": 50500.0,
      "unrealized_pnl": 0.5,
      "realized_pnl": 0.0,
      "pnl_percent": 1.0,
      "stop_loss": 49000.0,
      "take_profit": 52000.0,
      "opened_at": "2026-02-22T10:00:00",
      "closed_at": null
    }
  ],
  "total": 1
}
```

#### GET `/api/positions/{symbol}`

Get a specific position by symbol.

**Response:**
```json
{
  "id": 1,
  "symbol": "BTCUSDT",
  "side": "long",
  "quantity": 0.001,
  "entry_price": 50000.0,
  "current_price": 50500.0,
  "unrealized_pnl": 0.5,
  "realized_pnl": 0.0,
  "pnl_percent": 1.0,
  "stop_loss": 49000.0,
  "take_profit": 52000.0,
  "opened_at": "2026-02-22T10:00:00",
  "closed_at": null
}
```

#### POST `/api/positions/{symbol}/close`

Close a position.

**Response:**
```json
{
  "status": "success",
  "message": "Position closed",
  "symbol": "BTCUSDT"
}
```

---

### Strategies

#### GET `/api/strategies`

Get all available strategies.

**Response:**
```json
{
  "strategies": [
    {
      "name": "rsi",
      "version": "1.0.0",
      "description": "RSI overbought/oversold trading strategy",
      "initialized": true,
      "active": false,
      "parameters": {
        "period": 14,
        "oversold": 30,
        "overbought": 70
      }
    }
  ],
  "total": 1
}
```

#### GET `/api/strategies/{name}`

Get a specific strategy by name.

**Response:**
```json
{
  "name": "rsi",
  "version": "1.0.0",
  "description": "RSI overbought/oversold trading strategy",
  "initialized": true,
  "active": false,
  "parameters": {
    "period": 14,
    "oversold": 30,
    "overbought": 70
  },
  "symbols": ["BTCUSDT", "ETHUSDT"],
  "timeframe": "1h"
}
```

#### POST `/api/strategies/{name}/activate`

Activate a strategy.

**Request Body:**
```json
{
  "enabled": true,
  "parameters": {
    "period": 14,
    "oversold": 25,
    "overbought": 75
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Strategy 'rsi' activated",
  "name": "rsi"
}
```

#### POST `/api/strategies/{name}/deactivate`

Deactivate a strategy.

**Response:**
```json
{
  "status": "success",
  "message": "Strategy 'rsi' deactivated",
  "name": "rsi"
}
```

#### PUT `/api/strategies/{name}/parameters`

Update strategy parameters.

**Request Body:**
```json
{
  "period": 20,
  "oversold": 20,
  "overbought": 80
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Parameters updated for strategy 'rsi'",
  "name": "rsi",
  "parameters": {
    "period": 20,
    "oversold": 20,
    "overbought": 80
  }
}
```

---

## 🔌 WebSocket

### `/ws/stream`

WebSocket endpoint for realtime updates.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `client_id` | string | "default" | Unique client identifier |
| `channels` | string | - | Comma-separated channels to subscribe |

**Available Channels:**
- `orders` — Order updates
- `positions` — Position updates
- `signals` — Trading signals
- `prices` — Price updates
- `trades` — Trade executions

**Connect:**
```
ws://localhost:8000/ws/stream?client_id=myapp&channels=orders,positions
```

**Client Commands:**

Subscribe to channel:
```json
{
  "action": "subscribe",
  "channel": "signals"
}
```

Unsubscribe from channel:
```json
{
  "action": "unsubscribe",
  "channel": "orders"
}
```

Ping:
```json
{
  "action": "ping"
}
```

**Server Messages:**

Connected:
```json
{
  "type": "connected",
  "client_id": "myapp",
  "timestamp": "2026-02-22T10:30:00.000000"
}
```

Order update:
```json
{
  "type": "order",
  "action": "filled",
  "data": {
    "order_id": "12345678901",
    "symbol": "BTCUSDT",
    "side": "buy",
    "quantity": 0.001,
    "price": 50000.0
  }
}
```

Signal:
```json
{
  "type": "signal",
  "data": {
    "strategy": "rsi",
    "symbol": "BTCUSDT",
    "action": "buy",
    "strength": 0.85,
    "price": 50000.0,
    "rsi": 28.5
  }
}
```

Pong:
```json
{
  "type": "pong",
  "timestamp": "2026-02-22T10:30:05.000000"
}
```

#### GET `/ws/stats`

Get WebSocket connection statistics.

**Response:**
```json
{
  "total_connections": 5,
  "channels": {
    "client1": ["orders", "positions"],
    "client2": ["*"]
  }
}
```

---

## 📊 Models

### Order

```json
{
  "id": 1,
  "exchange_order_id": "12345678901",
  "symbol": "BTCUSDT",
  "side": "buy",
  "type": "market",
  "quantity": 0.001,
  "price": null,
  "filled_quantity": 0.001,
  "average_price": 50000.0,
  "status": "filled",
  "strategy_name": "rsi",
  "created_at": "2026-02-22T10:30:00",
  "updated_at": "2026-02-22T10:30:05"
}
```

### Position

```json
{
  "id": 1,
  "symbol": "BTCUSDT",
  "side": "long",
  "quantity": 0.001,
  "entry_price": 50000.0,
  "current_price": 50500.0,
  "unrealized_pnl": 0.5,
  "realized_pnl": 0.0,
  "pnl_percent": 1.0,
  "stop_loss": 49000.0,
  "take_profit": 52000.0,
  "opened_at": "2026-02-22T10:00:00",
  "closed_at": null
}
```

### Signal

```json
{
  "strategy": "rsi",
  "symbol": "BTCUSDT",
  "action": "buy",
  "strength": 0.85,
  "price": 50000.0,
  "stop_loss": 49000.0,
  "take_profit": 52000.0,
  "metadata": {
    "rsi": 28.5,
    "condition": "oversold"
  },
  "timestamp": "2026-02-22T10:30:00"
}
```

---

## ❌ Error Handling

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 401 | Unauthorized (invalid API key) |
| 404 | Not Found |
| 429 | Too Many Requests (rate limit) |
| 500 | Internal Server Error |

### Example Error

**Request:**
```
GET /api/orders/nonexistent
```

**Response (404):**
```json
{
  "detail": "Order not found"
}
```

---

## 📚 Interactive Documentation

FastAPI provides interactive API documentation:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

These pages allow you to:
- Browse all endpoints
- View request/response schemas
- Test API calls directly from the browser

---

*Last updated: 22 февраля 2026*
