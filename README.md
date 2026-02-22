# 📱 Crypto Trader

Автоматизированная система для трейдинга криптовалютными активами, работающая на Android через Termux.

[![Status](https://img.shields.io/badge/status-alpha-yellow)](https://github.com/JeBance/crypto-trader)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](https://github.com/JeBance/crypto-trader)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 🚀 Возможности

- **Поддержка бирж:** Binance, Bybit (через API)
- **Торговые стратегии:** RSI, MACD, SMA/EMA Crossover
- **Технические индикаторы:** RSI, MACD, SMA, EMA
- **Realtime уведомления:** Telegram, WebSocket
- **Веб-интерфейс:** React SPA с realtime обновлениями
- **Paper Trading:** Тестирование стратегий без риска
- **Гибкая архитектура:** Плагины для стратегий и бирж

---

## 📋 Требования

### Для запуска на Android:
- Устройство на базе **Android**
- Установленное приложение **Termux** (рекомендуется с F-Droid)
- Python 3.10+
- Node.js 18+ (для frontend)

### Для разработки:
- Python 3.10+
- Node.js 18+
- Git

---

## ⚙️ Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/JeBance/crypto-trader.git
cd crypto-trader
```

### 2. Установка Backend

```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r backend/requirements.txt
```

### 3. Установка Frontend

```bash
cd frontend
npm install
cd ..
```

### 4. Настройка конфигурации

```bash
# Backend
cp .env.example .env
# Отредактируйте .env с вашими API ключами

# Frontend
cp frontend/.env.example frontend/.env
```

### 5. Быстрая установка (Termux)

```bash
bash scripts/install.sh
```

---

## ▶️ Запуск

### Backend

```bash
# Активировать venv
source venv/bin/activate

# Запуск сервера
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Или через скрипт
bash scripts/start.sh
```

### Frontend (разработка)

```bash
cd frontend
npm run dev
```

### Production сборка Frontend

```bash
cd frontend
npm run build
# Файлы будут в frontend/dist/
```

---

## 🌐 Доступ к приложению

После запуска:

| Компонент | URL |
|-----------|-----|
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| Frontend (dev) | http://localhost:3000 |
| Frontend (prod) | https://jebance.github.io/crypto-trader/ |

---

## 📁 Структура проекта

```
crypto-trader/
├── backend/
│   ├── app/
│   │   ├── api/           # REST API endpoints
│   │   ├── core/          # Core модуль (events, exceptions, types)
│   │   ├── exchanges/     # Exchange плагины (Binance, Bybit)
│   │   ├── indicators/    # Технические индикаторы
│   │   ├── models/        # SQLAlchemy модели
│   │   ├── notifications/ # Notification плагины (Telegram)
│   │   ├── plugins/       # Система плагинов
│   │   ├── services/      # Бизнес-логика (OrderManager, PositionManager)
│   │   ├── strategies/    # Trading стратегии (RSI, MACD)
│   │   ├── websocket/     # WebSocket handlers
│   │   ├── main.py        # Точка входа FastAPI
│   │   ├── config.py      # Конфигурация
│   │   ├── database.py    # База данных
│   │   └── logger.py      # Логирование
│   ├── tests/             # Тесты
│   └── requirements.txt   # Зависимости Python
│
├── frontend/
│   ├── src/
│   │   ├── components/    # React компоненты
│   │   ├── pages/         # Страницы приложения
│   │   ├── services/      # API и WebSocket клиенты
│   │   ├── store/         # Redux store
│   │   ├── App.tsx        # Корневой компонент
│   │   └── main.tsx       # Точка входа
│   ├── public/            # Статические файлы
│   └── package.json       # Зависимости Node.js
│
├── scripts/
│   ├── install.sh         # Скрипт установки
│   └── start.sh           # Скрипт запуска
│
├── docs/
│   └── API.md             # Документация API
│
├── .env.example           # Шаблон переменных окружения
├── config.yaml.example    # Шаблон конфигурации стратегий
├── ROADMAP.md             # План разработки
├── AGENT.md               # Руководство для ИИ-агента
├── ARCHITECTURE.md        # Описание архитектуры
├── CONTRIBUTING.md        # Гайд по внесению изменений
└── DECISIONS.md           # Архитектурные решения (ADR)
```

---

## 🔌 API Endpoints

### Health
- `GET /api/health` — Health check
- `GET /api/health/status` — System status

### Configuration
- `GET /api/config` — Get configuration
- `GET /api/config/exchanges` — Exchange configs

### Orders
- `GET /api/orders` — Get orders
- `POST /api/orders` — Create order
- `DELETE /api/orders/{id}` — Cancel order

### Positions
- `GET /api/positions` — Get positions
- `POST /api/positions/{symbol}/close` — Close position

### Strategies
- `GET /api/strategies` — Get strategies
- `POST /api/strategies/{name}/activate` — Activate strategy
- `POST /api/strategies/{name}/deactivate` — Deactivate strategy

### WebSocket
- `WS /ws/stream` — Realtime updates

Полная документация: [/docs/API.md](docs/API.md) или http://localhost:8000/docs

---

## 📊 Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                  Frontend (React SPA)                   │
│  Dashboard │ Positions │ Orders │ Strategies │ Settings │
└─────────────────────────────────────────────────────────┘
              ↕ REST API / WebSocket ↕
┌─────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   Plugins   │  │    Core     │  │    Services     │  │
│  │  Exchange   │  │   Config    │  │  Order Manager  │  │
│  │  Strategy   │  │   Events    │  │  Position Mgr   │  │
│  │  Notifier   │  │   Logger    │  │  Data Service   │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
              ↕ External APIs ↕
┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐
│   Binance   │  │    Bybit    │  │   Telegram Bot API  │
└─────────────┘  └─────────────┘  └─────────────────────┘
```

Подробная архитектура: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🧪 Тестирование

### Backend

```bash
pytest backend/tests/ -v --cov=app
```

### Frontend

```bash
cd frontend
npm test
```

---

## 📈 ROADMAP

Текущий статус: **Этап 6 завершен** (Frontend UI)

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
| 9. Testing | 🔄 | Тесты (частично) |
| 10. Release v1.0 | ⏳ | Финальный релиз |

Полный план: [ROADMAP.md](ROADMAP.md)

---

## ⚠️ Предупреждение о рисках

> **ВАЖНО:** Использование торговых ботов связано с высоким финансовым риском.

- Этот код предоставляется «как есть» (AS IS)
- Не является финансовой рекомендацией
- Тестируйте стратегию на демо-счете перед использованием реальных средств
- Никогда не передавайте свои API-ключи третьим лицам

---

## 📄 Лицензия

MIT License — см. [LICENSE](LICENSE) файл

---

## 🔗 Ссылки

- [GitHub Repository](https://github.com/JeBance/crypto-trader)
- [API Documentation](docs/API.md)
- [Architecture](ARCHITECTURE.md)
- [Contributing Guide](CONTRIBUTING.md)
- [AI Agent Guide](AGENT.md)

---

## 🤝 Вклад в проект

См. [CONTRIBUTING.md](CONTRIBUTING.md) для информации о том, как внести свой вклад.

---

*Последнее обновление: 22 февраля 2026*
