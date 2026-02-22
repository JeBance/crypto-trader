# 🤖 AI Agent Context — Crypto Trader v1.0

**Контекст для продолжения разработки на смартфоне**

---

## 📋 Текущий статус проекта

**Версия:** 1.0.0 (Production Release)  
**Дата:** 22 февраля 2026  
**Статус:** ✅ Все этапы завершены

### Завершённые этапы (10/10)

1. ✅ **Foundation** — Базовая архитектура, плагины, Event Bus
2. ✅ **Core Backend** — FastAPI, WebSocket, сервисы
3. ✅ **Exchange Integration** — Binance, Bybit плагины
4. ✅ **Strategies & Indicators** — RSI, Crossover, MACD
5. ✅ **Risk Management** — RiskManager, BacktestEngine
6. ✅ **Frontend UI** — React SPA (Dashboard, Positions, Orders, Strategies, Settings)
7. ✅ **Notifications** — Telegram notifier
8. ✅ **Installation** — Auto-installer (setup.sh, run.sh)
9. ✅ **Self-Healing Server** — Auto-restart, auto-update
10. ✅ **Testing & Quality** — CI/CD, 65+ тестов

---

## 📁 Структура проекта

```
crypto-trader/
├── backend/app/
│   ├── api/              # REST API endpoints
│   │   ├── health.py     # Health check
│   │   ├── config.py     # Configuration API
│   │   ├── orders.py     # Orders API
│   │   ├── positions.py  # Positions API
│   │   └── strategies.py # Strategies API
│   │
│   ├── core/             # Core module
│   │   ├── events.py     # Event Bus (pub/sub)
│   │   ├── exceptions.py # Custom exceptions
│   │   └── types.py      # Data types (Candle, Order, etc.)
│   │
│   ├── exchanges/        # Exchange plugins
│   │   ├── binance.py    # Binance exchange
│   │   └── bybit.py      # Bybit exchange
│   │
│   ├── indicators/       # Technical indicators
│   │   ├── sma.py        # Simple Moving Average
│   │   ├── ema.py        # Exponential Moving Average
│   │   ├── rsi.py        # Relative Strength Index
│   │   └── macd.py       # MACD indicator
│   │
│   ├── models/           # SQLAlchemy models
│   │   ├── candle.py     # Candlestick data
│   │   ├── order.py      # Order data
│   │   ├── position.py   # Position data
│   │   └── trade.py      # Trade data
│   │
│   ├── notifications/    # Notification plugins
│   │   └── telegram.py   # Telegram bot
│   │
│   ├── plugins/          # Plugin system
│   │   ├── base.py       # Base plugin classes
│   │   └── manager.py    # Plugin manager
│   │
│   ├── services/         # Business logic
│   │   ├── order_manager.py
│   │   ├── position_manager.py
│   │   ├── data_service.py
│   │   ├── strategy_executor.py
│   │   ├── risk_manager.py
│   │   └── backtester.py
│   │
│   ├── strategies/       # Trading strategies
│   │   ├── rsi.py        # RSI strategy
│   │   ├── crossover.py  # SMA/EMA crossover
│   │   └── macd.py       # MACD strategy
│   │
│   ├── websocket/        # WebSocket handlers
│   │   ├── manager.py    # Connection manager
│   │   └── routes.py     # WebSocket routes
│   │
│   ├── self_healing/     # Self-healing components
│   │   ├── supervisor.py       # Service supervisor
│   │   ├── updater.py          # Auto-updater
│   │   └── health_monitor.py   # Health checks
│   │
│   ├── main.py           # FastAPI application
│   ├── config.py         # Configuration
│   ├── database.py       # Database setup
│   └── logger.py         # Logging setup
│
├── frontend/src/
│   ├── components/       # React components
│   │   ├── ui/           # Base UI components
│   │   └── layout/       # Layout components
│   │
│   ├── pages/            # Application pages
│   │   ├── Dashboard.tsx
│   │   ├── Positions.tsx
│   │   ├── Orders.tsx
│   │   ├── Strategies.tsx
│   │   └── Settings.tsx
│   │
│   ├── services/         # API clients
│   │   ├── api.ts        # REST API client
│   │   └── websocket.ts  # WebSocket client
│   │
│   ├── store/            # Redux store
│   │   └── index.ts
│   │
│   ├── App.tsx           # Root component
│   └── main.tsx          # Entry point
│
├── backend/tests/        # Unit & integration tests
│   ├── test_indicators.py
│   ├── test_events.py
│   ├── test_websocket.py
│   ├── test_data_service.py
│   ├── test_rsi_strategy.py
│   ├── test_risk_manager.py
│   └── test_integration.py
│
├── docs/                 # Documentation
│   ├── API.md
│   ├── INSTALL.md
│   ├── USER_GUIDE.md
│   ├── STRATEGIES.md
│   ├── SELF_HEALING_SERVER.md
│   ├── TERMUX_SETUP.md
│   ├── ARCHITECTURE.md
│   ├── CONTRIBUTING.md
│   └── DECISIONS.md
│
├── .github/workflows/
│   └── ci-cd.yml         # CI/CD pipeline
│
├── scripts/              # Bash scripts
│   ├── setup.sh          # Auto-installer
│   └── run.sh            # Server runner
│
├── run_server.py         # Self-healing server
├── README.md             # Main documentation
├── ROADMAP.md            # Development roadmap
├── CHANGELOG.md          # Version history
├── AGENT.md              # AI agent guide (this file)
└── .env.example          # Environment template
```

---

## 🎯 Ключевые компоненты

### 1. Self-Healing Server

**Файлы:** `run_server.py`, `run.sh`, `backend/app/self_healing/`

**Функционал:**
- Авто-перезапуск при падении
- Авто-обновление из Git
- Health monitoring
- Real-time логирование

**Запуск:**
```bash
bash run.sh              # Обычный запуск
bash run.sh --debug      # Debug режим
bash run.sh --no-auto-update  # Без авто-обновления
```

### 2. Plugin System

**Файлы:** `backend/app/plugins/`

**Базовые классы:**
- `Plugin` — базовый класс
- `ExchangePlugin` — для бирж
- `StrategyPlugin` — для стратегий
- `NotifierPlugin` — для уведомлений

**Пример создания плагина:**
```python
from app.plugins.base import StrategyPlugin

class MyStrategy(StrategyPlugin):
    name = "my_strategy"
    
    async def on_candle(self, candle):
        # Generate signal
        return Signal(action=SignalAction.BUY, ...)
```

### 3. Event Bus

**Файлы:** `backend/app/core/events.py`

**Использование:**
```python
from app.core.events import publish, subscribe, EventType

# Subscribe
subscribe(EventType.ORDER_CREATED, my_handler)

# Publish
await publish(EventType.ORDER_CREATED, {"order_id": "123"})
```

### 4. Risk Management

**Файлы:** `backend/app/services/risk_manager.py`

**Функционал:**
- Position sizing
- Stop-loss / Take-profit
- Risk checks
- Drawdown tracking

**Пример:**
```python
from app.services.risk_manager import RiskManager, RiskConfig

rm = RiskManager(RiskConfig(max_risk_per_trade=1.0))
rm.set_capital(10000)

result = rm.calculate_position_size(
    entry_price=50000,
    stop_loss_price=49000,
)
```

### 5. Backtest Engine

**Файлы:** `backend/app/services/backtester.py`

**Использование:**
```python
from app.services.backtester import BacktestEngine, BacktestConfig

engine = BacktestEngine(BacktestConfig(initial_capital=10000))
result = await engine.run(strategy, candles, "BTCUSDT")

print(f"Return: {result.total_return}%")
print(f"Win Rate: {result.win_rate}%")
```

---

## 🧪 Тестирование

### Запуск тестов

```bash
# Активировать venv
source venv/bin/activate

# Все тесты
pytest backend/tests/ -v

# С покрытием
pytest backend/tests/ -v --cov=backend/app

# Конкретный файл
pytest backend/tests/test_risk_manager.py -v
```

### Структура тестов

| Файл | Тестов | Описание |
|------|--------|----------|
| `test_indicators.py` | 16 | SMA, EMA, RSI, MACD |
| `test_events.py` | 15 | Event Bus |
| `test_websocket.py` | 10 | WebSocket manager |
| `test_data_service.py` | 12 | Data service + cache |
| `test_rsi_strategy.py` | 10 | RSI strategy |
| `test_risk_manager.py` | 25 | Risk management |
| `test_integration.py` | 10+ | Integration tests |

---

## 📖 Документация

### Основная
- `README.md` — Главная страница
- `CHANGELOG.md` — История изменений
- `ROADMAP.md` — План разработки (100% завершено)

### Для пользователей
- `docs/INSTALL.md` — Установка
- `docs/TERMUX_SETUP.md` — Установка на Android
- `docs/USER_GUIDE.md` — Работа через UI
- `docs/STRATEGIES.md` — Стратегии

### Технические
- `docs/API.md` — API документация
- `docs/ARCHITECTURE.md` — Архитектура
- `docs/SELF_HEALING_SERVER.md` — Self-healing guide
- `docs/CONTRIBUTING.md` — Contributing guide
- `docs/DECISIONS.md` — Architectural decisions

---

## 🔧 Конфигурация

### Переменные окружения (.env)

```bash
# Application
APP_ENV=development
APP_DEBUG=true
APP_LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/crypto_trader.db

# Security
API_KEY=crypto-trader-default-key-change-in-production
SECRET_KEY=crypto-trader-default-secret-change-in-production

# Trading
TRADING_MODE=paper  # paper | live

# Binance (optional)
BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_TESTNET=true

# Bybit (optional)
BYBIT_API_KEY=
BYBIT_API_SECRET=
BYBIT_TESTNET=true

# Telegram (optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Risk
MAX_POSITION_SIZE_PERCENT=10
STOP_LOSS_PERCENT=2
TAKE_PROFIT_PERCENT=4
DAILY_LOSS_LIMIT_PERCENT=5
```

---

## 🚀 Следующие шаги (для продолжения разработки)

### Приоритетные задачи

1. **Добавить больше стратегий:**
   - Bollinger Bands
   - Stochastic Oscillator
   - Multi-strategy portfolio

2. **Улучшить UI:**
   - Графики (TradingView Lightweight Charts)
   - Real-time обновления через WebSocket
   - Мобильная адаптация

3. **Добавить биржи:**
   - OKX
   - Kraken
   - DEX интеграция

4. **Machine Learning:**
   - Предсказание трендов
   - Оптимизация параметров стратегий

5. **Cloud Sync:**
   - Синхронизация настроек
   - Backup/restore

### Идеи для v1.1.0

- [ ] OKX exchange plugin
- [ ] Bollinger Bands indicator
- [ ] Stochastic strategy
- [ ] TradingView charts in UI
- [ ] Multi-strategy portfolio
- [ ] Advanced backtesting with optimization
- [ ] Mobile app (React Native)

---

## 📞 Контакты и ресурсы

- **GitHub:** https://github.com/JeBance/crypto-trader
- **Issues:** https://github.com/JeBance/crypto-trader/issues
- **API Docs:** http://localhost:8000/docs

---

## 🎯 Quick Start для ИИ-агента

Если нужно продолжить разработку:

1. **Изучить структуру:**
   ```bash
   tree -L 3 -I '__pycache__|node_modules|venv'
   ```

2. **Проверить статус:**
   ```bash
   git status
   git log -n 5 --oneline
   ```

3. **Запустить тесты:**
   ```bash
   source venv/bin/activate
   pytest backend/tests/ -v
   ```

4. **Запустить сервер:**
   ```bash
   bash run.sh --debug
   ```

5. **Открыть UI:**
   ```
   http://localhost:3000
   ```

---

*Контекст подготовлен: 22 февраля 2026*  
*Версия проекта: 1.0.0*  
*Статус: Production Ready*
