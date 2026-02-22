# 🏗️ ARCHITECTURE — Crypto Trader

Документ описывает архитектуру системы Crypto Trader.

---

## 📐 Обзор архитектуры

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            CLIENT LAYER                                 │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Web Browser (Android)                        │    │
│  │  ┌──────────────────────────────────────────────────────────┐   │    │
│  │  │              React SPA (GitHub Pages / Local)            │   │    │
│  │  │  Dashboard │ Positions │ Orders │ Strategies │ Settings  │   │    │
│  │  └──────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
         │                    │
         │ REST API (HTTP)    │ WebSocket (Realtime)
         ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          API GATEWAY LAYER                              │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    FastAPI Application                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │    │
│  │  │  REST API    │  │  WebSocket   │  │   Middleware         │   │    │
│  │  │  Endpoints   │  │  Manager     │  │   (Auth, CORS, Log)  │   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         BUSINESS LOGIC LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ Order        │  │ Position     │  │ Data         │  │ Risk       │  │
│  │ Manager      │  │ Manager      │  │ Service      │  │ Manager    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Strategy     │  │ Backtest     │  │ Event        │                  │
│  │ Executor     │  │ Engine       │  │ Bus          │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          PLUGIN LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Plugin Manager                               │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │    │
│  │  │  Exchange    │  │  Strategy    │  │   Notifier           │   │    │
│  │  │  Plugins     │  │  Plugins     │  │   Plugins            │   │    │
│  │  │  • Binance   │  │  • RSI       │  │   • Telegram         │   │    │
│  │  │  • Bybit     │  │  • MACD      │  │   • Email            │   │    │
│  │  │  • OKX       │  │  • Crossover │  │   • Push             │   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐           │
│  │  SQLite      │  │  Cache       │  │   External           │           │
│  │  Database    │  │  (LRU)       │  │   APIs               │           │
│  │              │  │              │  │   • Binance API      │           │
│  │  • Candles   │  │  • Tickers   │  │   • Bybit API        │           │
│  │  • Orders    │  │  • Orders    │  │   • OKX API          │           │
│  │  • Positions │  │  • Candles   │  │                      │           │
│  │  • Trades    │  │              │  │                      │           │
│  └──────────────┘  └──────────────┘  └──────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Компоненты

### 1. Frontend (React SPA)

**Технологии:** React 18, TypeScript, Vite, Material UI

**Компоненты:**
```
src/
├── components/
│   ├── ui/           # Базовые UI компоненты (Button, Input, Modal)
│   ├── layout/       # Layout (Header, Sidebar, Footer)
│   └── charts/       # Графики (TradingView Lightweight Charts)
├── pages/
│   ├── Dashboard     # Главная панель (статистика, активные стратегии)
│   ├── Positions     # Открытые позиции с PnL
│   ├── Orders        # История ордеров
│   ├── Strategies    # Управление стратегиями
│   └── Settings      # Настройки (биржи, риски, уведомления)
├── hooks/
│   ├── useWebSocket  # Подключение к WebSocket
│   ├── useOrders     # Запрос ордеров
│   └── usePositions  # Запрос позиций
├── services/
│   ├── api.ts        # REST API клиент
│   └── websocket.ts  # WebSocket клиент
└── store/
    └── slices/       # Redux slices (orders, positions, settings)
```

**Потоки данных:**
```
User Action → Component → Redux Action → API Call → Backend
                                              ↓
Component ← Redux Update ← WebSocket ← Backend Event
```

---

### 2. Backend (FastAPI)

**Технологии:** Python 3.10+, FastAPI, SQLAlchemy, Pydantic

#### 2.1 Core Module

```python
# app/core/events.py
class EventBus:
    """Центральная шина событий для loose coupling"""
    
    def subscribe(self, event_type: str, handler: Callable)
    def publish(self, event_type: str, data: dict)
    def unsubscribe(self, event_type: str, handler: Callable)

# События системы:
# - ORDER_CREATED, ORDER_FILLED, ORDER_CANCELLED
# - POSITION_OPENED, POSITION_CLOSED, POSITION_UPDATED
# - SIGNAL_GENERATED, STRATEGY_STARTED, STRATEGY_STOPPED
# - PRICE_UPDATED, CANDLE_CLOSED
```

```python
# app/core/exceptions.py
class CryptoTraderException(Exception)
class ExchangeError(CryptoTraderException)
class StrategyError(CryptoTraderException)
class OrderError(CryptoTraderException)
class ConfigurationError(CryptoTraderException)
```

#### 2.2 Plugin System

```python
# app/plugins/base.py
class Plugin(ABC):
    """Базовый класс для всех плагинов"""
    
    name: str
    version: str
    description: str
    
    @abstractmethod
    async def initialize(self) -> None: ...
    
    @abstractmethod
    async def shutdown(self) -> None: ...

class ExchangePlugin(Plugin):
    """Базовый класс для бирж"""
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker: ...
    
    @abstractmethod
    async def get_candles(self, symbol: str, timeframe: str, limit: int) -> list[Candle]: ...
    
    @abstractmethod
    async def create_order(self, order: OrderRequest) -> Order: ...
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> Order: ...
    
    @abstractmethod
    async def get_balance(self) -> dict[str, Balance]: ...

class StrategyPlugin(Plugin):
    """Базовый класс для стратегий"""
    
    @abstractmethod
    async def on_candle(self, candle: Candle) -> Optional[Signal]: ...
    
    @abstractmethod
    def get_parameters(self) -> dict: ...
    
    @abstractmethod
    def set_parameters(self, params: dict) -> None: ...

class NotifierPlugin(Plugin):
    """Базовый класс для уведомлений"""
    
    @abstractmethod
    async def send(self, message: str, level: str = "info") -> None: ...
```

#### 2.3 Services

```python
# app/services/order_manager.py
class OrderManager:
    """Управление ордерами"""
    
    async def create_market_order(self, symbol: str, side: str, quantity: float) -> Order
    async def create_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Order
    async def cancel_order(self, order_id: str) -> Order
    async def get_orders(self, status: str = None) -> list[Order]
    async def sync_orders(self) -> None  # Синхронизация с биржей

# app/services/position_manager.py
class PositionManager:
    """Управление позициями"""
    
    async def get_positions(self) -> list[Position]
    async def get_position(self, symbol: str) -> Optional[Position]
    async def update_pnl(self) -> None  # Обновление PnL всех позиций
    async def close_position(self, symbol: str) -> Order
    async def close_all_positions(self) -> list[Order]

# app/services/data_service.py
class DataService:
    """Получение и кэширование рыночных данных"""
    
    async def get_candles(self, symbol: str, timeframe: str, limit: int) -> list[Candle]
    async def get_ticker(self, symbol: str) -> Ticker
    async def subscribe_candles(self, symbol: str, timeframe: str) -> AsyncIterator[Candle]

# app/services/risk_manager.py
class RiskManager:
    """Управление рисками"""
    
    def check_order(self, order: OrderRequest) -> RiskCheckResult
    def calculate_position_size(self, capital: float, risk_percent: float, stop_loss: float) -> float
    def check_drawdown_limit(self) -> bool
    def check_daily_loss_limit(self) -> bool
```

---

### 3. Data Models

```python
# app/models/candle.py
class Candle(Base):
    __tablename__ = "candles"
    
    id: int = Column(Integer, primary_key=True)
    symbol: str = Column(String, nullable=False)
    timeframe: str = Column(String, nullable=False)
    timestamp: datetime = Column(DateTime, nullable=False)
    open: float = Column(Float, nullable=False)
    high: float = Column(Float, nullable=False)
    low: float = Column(Float, nullable=False)
    close: float = Column(Float, nullable=False)
    volume: float = Column(Float, nullable=False)
    
    __table_args__ = (UniqueConstraint('symbol', 'timeframe', 'timestamp'),)

# app/models/order.py
class Order(Base):
    __tablename__ = "orders"
    
    id: int = Column(Integer, primary_key=True)
    exchange_order_id: str = Column(String, unique=True)
    symbol: str = Column(String, nullable=False)
    side: str = Column(String, nullable=False)  # buy, sell
    type: str = Column(String, nullable=False)  # market, limit
    quantity: float = Column(Float, nullable=False)
    price: float = Column(Float, nullable=True)
    status: str = Column(String, nullable=False)  # pending, filled, cancelled, rejected
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, onupdate=datetime.utcnow)

# app/models/position.py
class Position(Base):
    __tablename__ = "positions"
    
    id: int = Column(Integer, primary_key=True)
    symbol: str = Column(String, nullable=False, unique=True)
    side: str = Column(String, nullable=False)  # long, short
    quantity: float = Column(Float, nullable=False)
    entry_price: float = Column(Float, nullable=False)
    current_price: float = Column(Float, nullable=True)
    unrealized_pnl: float = Column(Float, nullable=True)
    realized_pnl: float = Column(Float, default=0)
    opened_at: datetime = Column(DateTime, default=datetime.utcnow)
    closed_at: datetime = Column(DateTime, nullable=True)

# app/models/trade.py
class Trade(Base):
    __tablename__ = "trades"
    
    id: int = Column(Integer, primary_key=True)
    order_id: int = Column(Integer, ForeignKey("orders.id"))
    symbol: str = Column(String, nullable=False)
    side: str = Column(String, nullable=False)
    quantity: float = Column(Float, nullable=False)
    price: float = Column(Float, nullable=False)
    fee: float = Column(Float, default=0)
    fee_currency: str = Column(String, nullable=True)
    executed_at: datetime = Column(DateTime, default=datetime.utcnow)
```

---

## 🔄 Потоки данных

### 1. Получение свечей и генерация сигнала

```
┌──────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Exchange │────▶│ DataService │────▶│ Strategy     │────▶│ EventBus    │
│   API    │     │  (Cache)    │     │  Executor    │     │             │
└──────────┘     └─────────────┘     └──────────────┘     └─────────────┘
                                                               │
                                                               ▼
┌──────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Telegram │◀────│ Notifier    │◀────│ Order       │◀────│ Signal      │
│   Bot    │     │  Plugin     │     │  Manager     │     │  (BUY/SELL)│
└──────────┘     └─────────────┘     └──────────────┘     └─────────────┘
```

### 2. WebSocket realtime обновления

```
┌──────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Backend  │────▶│ WebSocket   │────▶│  Frontend   │────▶│    React    │
│  Events  │     │  Manager    │     │  Client     │     │  Components │
└──────────┘     └─────────────┘     └──────────────┘     └─────────────┘
```

### 3. REST API запрос

```
┌──────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Frontend │────▶│ FastAPI     │────▶│  Service     │────▶│  Database   │
│  (HTTP)  │     │  Router     │     │  Layer       │     │  (SQLite)   │
└──────────┘     └─────────────┘     └──────────────┘     └─────────────┘
```

---

## 🔌 Plugin Architecture

### Регистрация плагинов

```python
# app/plugins/manager.py
class PluginManager:
    def __init__(self):
        self.plugins: dict[str, Plugin] = {}
        self.exchange_plugins: dict[str, ExchangePlugin] = {}
        self.strategy_plugins: dict[str, StrategyPlugin] = {}
        self.notifier_plugins: dict[str, NotifierPlugin] = {}
    
    def discover(self, plugin_dir: Path) -> None:
        """Автоматическое обнаружение плагинов"""
        for file in plugin_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue
            module = importlib.import_module(f"app.plugins.{file.stem}")
            self._register_plugin(module)
    
    def register(self, plugin: Plugin) -> None:
        """Регистрация плагина"""
        self.plugins[plugin.name] = plugin
        
        if isinstance(plugin, ExchangePlugin):
            self.exchange_plugins[plugin.name] = plugin
        elif isinstance(plugin, StrategyPlugin):
            self.strategy_plugins[plugin.name] = plugin
        elif isinstance(plugin, NotifierPlugin):
            self.notifier_plugins[plugin.name] = plugin
    
    async def initialize_all(self) -> None:
        """Инициализация всех плагинов"""
        for plugin in self.plugins.values():
            await plugin.initialize()
    
    async def shutdown_all(self) -> None:
        """Остановка всех плагинов"""
        for plugin in self.plugins.values():
            await plugin.shutdown()
```

### Пример плагина биржи

```python
# app/exchanges/binance.py
from app.plugins.exchange import ExchangePlugin

class BinanceExchange(ExchangePlugin):
    name = "binance"
    version = "1.0.0"
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://testnet.binance.vision" if testnet else "https://api.binance.com"
    
    async def initialize(self) -> None:
        # Проверка подключения, загрузка информации о парах
        pass
    
    async def get_ticker(self, symbol: str) -> Ticker:
        # GET /api/v3/ticker/24hr
        pass
    
    async def get_candles(self, symbol: str, timeframe: str, limit: int) -> list[Candle]:
        # GET /api/v3/klines
        pass
    
    async def create_order(self, order: OrderRequest) -> Order:
        # POST /api/v3/order
        pass
```

### Пример плагина стратегии

```python
# app/strategies/rsi.py
from app.plugins.strategy import StrategyPlugin
from app.indicators.rsi import RSI

class RSIStrategy(StrategyPlugin):
    name = "rsi"
    version = "1.0.0"
    
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        self.rsi = RSI(period=period)
        self.oversold = oversold
        self.overbought = overbought
    
    async def on_candle(self, candle: Candle) -> Optional[Signal]:
        rsi_value = self.rsi.calculate(candle.close_prices)
        
        if rsi_value < self.oversold:
            return Signal(action="BUY", strength=0.8, metadata={"rsi": rsi_value})
        elif rsi_value > self.overbought:
            return Signal(action="SELL", strength=0.8, metadata={"rsi": rsi_value})
        
        return None
```

---

## 🔐 Безопасность

### Хранение секретов

```
.env                    # Локальный файл (не коммитить!)
BINANCE_API_KEY=xxx
BINANCE_API_SECRET=yyy
TELEGRAM_BOT_TOKEN=zzz

.env.example            # Шаблон для пользователей (коммитить)
BINANCE_API_KEY=
BINANCE_API_SECRET=
TELEGRAM_BOT_TOKEN=
```

### Валидация API запросов

```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
```

---

## 📊 Масштабируемость

### Ограничения Termux

| Параметр | Ограничение | Рекомендация |
|----------|-------------|--------------|
| RAM | 1-4 GB | Использовать LRU кэш, не хранить всё в памяти |
| CPU | 4-8 ядер | Использовать asyncio, не блокировать поток |
| Storage | Зависит от устройства | SQLite, ротация логов |
| Network | WiFi/Mobile | Retry logic, reconnect WebSocket |

### Оптимизации

1. **Кэширование:** LRU кэш для свечей и тикеров
2. **Batch запросы:** Группировка API запросов к биржам
3. **Lazy loading:** Загрузка плагинов по требованию
4. **Connection pooling:** Пул соединений для SQLite

---

## 📈 Мониторинг

### Health Check Endpoint

```python
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "database": await check_database(),
        "exchanges": await check_exchanges(),
        "strategies": await check_strategies(),
    }
```

### Метрики

- Количество активных стратегий
- Количество ордеров в секунду
- Задержка WebSocket сообщений
- PnL по позициям
- Drawdown

---

*Последнее обновление: 22 февраля 2026*
