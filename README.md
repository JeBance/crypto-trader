# 📱 Crypto Trader

Автоматизированная система для трейдинга криптовалютными активами, работающая на Android через Termux.

[![Status](https://img.shields.io/badge/status-alpha-yellow)](https://github.com/JeBance/crypto-trader)
[![Version](https://img.shields.io/badge/version-0.2.0-blue)](https://github.com/JeBance/crypto-trader)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Android%20%7C%20Linux%20%7C%20macOS-orange)](https://github.com/JeBance/crypto-trader)

---

## 🔥 Новые возможности v0.2.0

### Self-Healing Server
- ✅ **Авто-перезапуск** при падении сервиса
- ✅ **Авто-обновление** из Git репозитория
- ✅ **Health Monitoring** компонентов
- ✅ **Real-time логи** в терминале
- ✅ **Graceful Shutdown**

### Запуск в одну команду
```bash
bash run.sh
```

---

## 🚀 Возможности

### Trading
- **Поддержка бирж:** Binance, Bybit (через API)
- **Торговые стратегии:** RSI, MACD, SMA/EMA Crossover
- **Технические индикаторы:** RSI, MACD, SMA, EMA
- **Paper Trading:** Тестирование без риска

### Notifications
- **Telegram:** Уведомления о сделках и сигналах
- **WebSocket:** Realtime обновления для frontend

### Interface
- **Веб-интерфейс:** React SPA с realtime данными
- **Dashboard:** Статистика, позиции, PnL
- **Mobile-friendly:** Адаптивный дизайн

### Infrastructure
- **Self-Healing:** Авто-восстановление при сбоях
- **Auto-Update:** Обновление из Git
- **Health Checks:** Мониторинг состояния

---

## 📋 Требования

### Для запуска на Android:
- Устройство на базе **Android**
- Установленное приложение **Termux** (рекомендуется с F-Droid)
- Python 3.10+
- Node.js 18+ (для frontend)
- Git

### Для разработки:
- Python 3.10+
- Node.js 18+
- Git
- Docker (опционально)

---

## ⚙️ Быстрый старт

### 1. Клонирование

```bash
git clone https://github.com/JeBance/crypto-trader.git
cd crypto-trader
```

### 2. Автоматическая установка (рекомендуется)

**Одна команда установит всё:**

```bash
bash setup.sh
```

**Что сделает setup.sh:**
- ✅ Проверит Python, Git, Node.js
- ✅ Установит отсутствующие пакеты
- ✅ Создаст виртуальное окружение
- ✅ Установит Python зависимости
- ✅ Установит Frontend зависимости
- ✅ Создаст .env и config.yaml

**Опции:**
```bash
# Полная переустановка
bash setup.sh --force

# Без frontend
bash setup.sh --no-frontend

# Пропустить системные пакеты
bash setup.sh --skip-packages
```

### 3. Запуск сервера

```bash
# Простой запуск (setup запустится автоматически если нужно)
bash run.sh

# Debug режим
bash run.sh --debug

# Только установка без запуска
bash run.sh --setup
```

### 4. Ручная установка (если auto не работает)

```bash
# Termux
pkg update && pkg upgrade
pkg install python git curl wget nodejs

# Linux
sudo apt update
sudo apt install python3 python3-pip python3-venv git curl nodejs

# macOS
brew install python git node

# Затем
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### 5. Настройка

```bash
# Копирование конфигурации
cp .env.example .env
cp config.yaml.example config.yaml

# Редактирование .env
nano .env

# Вставьте ваши API ключи:
# BINANCE_API_KEY=your_key_here
# BINANCE_API_SECRET=your_secret_here
# TELEGRAM_BOT_TOKEN=your_bot_token
# TELEGRAM_CHAT_ID=your_chat_id
```

### 6. Доступ к приложению

Откройте в браузере телефона или компьютера:

| Компонент | URL |
|-----------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |

---

## 📁 Структура проекта

```
crypto-trader/
├── backend/
│   ├── app/
│   │   ├── api/               # REST API endpoints
│   │   │   ├── health.py      # Health check endpoints
│   │   │   ├── config.py      # Configuration API
│   │   │   ├── orders.py      # Orders API
│   │   │   ├── positions.py   # Positions API
│   │   │   └── strategies.py  # Strategies API
│   │   │
│   │   ├── core/              # Core module
│   │   │   ├── events.py      # Event Bus (pub/sub)
│   │   │   ├── exceptions.py  # Custom exceptions
│   │   │   └── types.py       # Data types
│   │   │
│   │   ├── exchanges/         # Exchange plugins
│   │   │   ├── binance.py     # Binance exchange
│   │   │   └── bybit.py       # Bybit exchange
│   │   │
│   │   ├── indicators/        # Technical indicators
│   │   │   ├── sma.py         # Simple Moving Average
│   │   │   ├── ema.py         # Exponential Moving Average
│   │   │   ├── rsi.py         # Relative Strength Index
│   │   │   └── macd.py        # MACD indicator
│   │   │
│   │   ├── models/            # Database models
│   │   │   ├── candle.py      # Candlestick data
│   │   │   ├── order.py       # Order data
│   │   │   ├── position.py    # Position data
│   │   │   └── trade.py       # Trade data
│   │   │
│   │   ├── notifications/     # Notification plugins
│   │   │   └── telegram.py    # Telegram bot
│   │   │
│   │   ├── plugins/           # Plugin system
│   │   │   ├── base.py        # Base plugin classes
│   │   │   └── manager.py     # Plugin manager
│   │   │
│   │   ├── services/          # Business logic
│   │   │   ├── order_manager.py
│   │   │   ├── position_manager.py
│   │   │   ├── data_service.py
│   │   │   └── strategy_executor.py
│   │   │
│   │   ├── strategies/        # Trading strategies
│   │   │   └── rsi.py         # RSI strategy
│   │   │
│   │   ├── websocket/         # WebSocket handlers
│   │   │   ├── manager.py     # Connection manager
│   │   │   └── routes.py      # WebSocket routes
│   │   │
│   │   ├── self_healing/      # Self-healing components
│   │   │   ├── supervisor.py        # Service supervisor
│   │   │   ├── updater.py           # Auto-updater
│   │   │   └── health_monitor.py    # Health checks
│   │   │
│   │   ├── main.py            # FastAPI application
│   │   ├── config.py          # Configuration
│   │   ├── database.py        # Database setup
│   │   └── logger.py          # Logging setup
│   │
│   ├── tests/                 # Unit tests
│   │   ├── test_indicators.py
│   │   ├── test_events.py
│   │   ├── test_websocket.py
│   │   ├── test_data_service.py
│   │   └── test_rsi_strategy.py
│   │
│   └── requirements.txt       # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── ui/            # Base UI components
│   │   │   └── layout/        # Layout components
│   │   │
│   │   ├── pages/             # Application pages
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Positions.tsx
│   │   │   ├── Orders.tsx
│   │   │   ├── Strategies.tsx
│   │   │   └── Settings.tsx
│   │   │
│   │   ├── services/          # API clients
│   │   │   ├── api.ts         # REST API client
│   │   │   └── websocket.ts   # WebSocket client
│   │   │
│   │   ├── store/             # Redux store
│   │   │   └── index.ts
│   │   │
│   │   ├── App.tsx            # Root component
│   │   └── main.tsx           # Entry point
│   │
│   ├── public/                # Static files
│   ├── package.json           # Node dependencies
│   └── vite.config.ts         # Vite configuration
│
├── scripts/
│   ├── install.sh             # Installation script
│   ├── start.sh               # Start script
│   ├── hook_prerestart.sh     # Pre-restart hook
│   └── hook_postrestart.sh    # Post-restart hook
│
├── docs/
│   ├── API.md                 # API documentation
│   ├── SELF_HEALING_SERVER.md # Self-healing guide
│   ├── ARCHITECTURE.md        # Architecture guide
│   └── CONTRIBUTING.md        # Contributing guide
│
├── run_server.py              # Self-healing server
├── run.sh                     # Bash wrapper
├── .env.example               # Environment template
├── config.yaml.example        # Config template
├── README.md                  # This file
├── ROADMAP.md                 # Development roadmap
└── AGENT.md                   # AI agent guide
```

---

## 📖 Документация

### Основное
- 📘 [API Documentation](docs/API.md) — REST API и WebSocket endpoints
- 🔄 [Self-Healing Server](docs/SELF_HEALING_SERVER.md) — Руководство по авто-восстановлению
- 🏗️ [Architecture](docs/ARCHITECTURE.md) — Архитектура системы
- 🤝 [Contributing](docs/CONTRIBUTING.md) — Как внести вклад

### Для разработчиков
- 🤖 [AI Agent Guide](AGENT.md) — Руководство для ИИ-агента
- 📋 [Decisions](docs/DECISIONS.md) — Архитектурные решения (ADR)
- 🗺️ [ROADMAP](ROADMAP.md) — План разработки

---

## 🔌 API Endpoints

### Health & Status
```bash
GET /api/health              # Health check
GET /api/health/ready        # Readiness check
GET /api/health/status       # System status
```

### Configuration
```bash
GET /api/config              # Get configuration
GET /api/config/exchanges    # Exchange configs
GET /api/config/env          # Environment variables
```

### Orders
```bash
GET  /api/orders             # Get orders
GET  /api/orders/{id}        # Get order by ID
POST /api/orders             # Create order
DELETE /api/orders/{id}      # Cancel order
```

### Positions
```bash
GET  /api/positions          # Get positions
GET  /api/positions/{symbol} # Get position by symbol
POST /api/positions/{symbol}/close  # Close position
```

### Strategies
```bash
GET  /api/strategies         # Get strategies
GET  /api/strategies/{name}  # Get strategy by name
POST /api/strategies/{name}/activate    # Activate strategy
POST /api/strategies/{name}/deactivate  # Deactivate strategy
PUT  /api/strategies/{name}/parameters  # Update parameters
```

### WebSocket
```bash
WS /ws/stream                # Realtime updates
```

---

## 🧪 Тестирование

### Backend тесты

```bash
# Активировать venv
source venv/bin/activate

# Запустить тесты
pytest backend/tests/ -v

# С покрытием
pytest backend/tests/ -v --cov=app --cov-report=html
```

### Frontend тесты

```bash
cd frontend

# Запустить тесты
npm test

# С покрытием
npm test -- --coverage
```

---

## 📊 Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (React SPA)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Dashboard │ Positions │ Orders │ Strategies │ Settings │  │
│  └──────────────────────────────────────────────────────┘   │
│         ↕ REST API / WebSocket ↕                            │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              SELF-HEALING LAYER                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │   │
│  │  │  Supervisor  │  │  AutoUpdater │  │   Health   │ │   │
│  │  │  (restart)   │  │  (git pull)  │  │  Monitor   │ │   │
│  │  └──────────────┘  └──────────────┘  └────────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  APPLICATION LAYER                   │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │   │
│  │  │   Plugins   │  │   Core      │  │   Services   │ │   │
│  │  │  Exchange   │  │   Config    │  │   Order Mgr  │ │   │
│  │  │  Strategy   │  │   Events    │  │  Position Mgr│ │   │
│  │  │  Notifier   │  │   Logger    │  │  Data Service│ │   │
│  │  └─────────────┘  └─────────────┘  └──────────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
│         ↕ External APIs ↕                                   │
└─────────────────────────────────────────────────────────────┘
┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐
│   Binance    │  │    Bybit     │  │   Telegram Bot API   │
└──────────────┘  └──────────────┘  └──────────────────────┘
```

---

## ⚠️ Предупреждение о рисках

> **ВАЖНО:** Использование торговых ботов связано с высоким финансовым риском.

- Этот код предоставляется «как есть» (AS IS)
- Не является финансовой рекомендацией
- Тестируйте стратегию на демо-счете перед использованием реальных средств
- Никогда не передавайте свои API-ключи третьим лицам
- Используйте testnet режим для тестирования

---

## 📄 Лицензия

MIT License — см. [LICENSE](LICENSE) файл

---

## 🔗 Ссылки

- [GitHub Repository](https://github.com/JeBance/crypto-trader)
- [API Documentation](docs/API.md)
- [Self-Healing Guide](docs/SELF_HEALING_SERVER.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Contributing Guide](docs/CONTRIBUTING.md)
- [AI Agent Guide](AGENT.md)

---

## 🤝 Вклад в проект

См. [CONTRIBUTING.md](docs/CONTRIBUTING.md) для информации о том, как внести свой вклад.

---

## 📈 Статус проекта

| Этап | Статус | Описание |
|------|--------|----------|
| 1. Foundation | ✅ | Базовая архитектура, плагины, Event Bus |
| 2. Core Backend | ✅ | FastAPI, WebSocket, сервисы |
| 3. Exchange Integration | ✅ | Binance, Bybit плагины |
| 4. Strategies & Indicators | ✅ | RSI, MACD, SMA, EMA |
| 5. Risk Management | ⏳ | Управление рисками |
| 6. Frontend UI | ✅ | React приложение |
| 7. Notifications | ✅ | Telegram notifier |
| 8. Installation | ✅ | Скрипты установки |
| **9. Self-Healing Server** | ✅ | **Авто-восстановление и обновление** |
| 10. Testing | 🔄 | Тесты (частично) |
| 11. Release v1.0 | ⏳ | Финальный релиз |

---

*Последнее обновление: 22 февраля 2026*
