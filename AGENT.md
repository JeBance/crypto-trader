# 🤖 AI Agent Guide — Crypto Trader

Руководство для ИИ-агента по разработке и поддержке проекта Crypto Trader.

---

## 📖 О проекте

**Crypto Trader** — автоматизированная система для трейдинга криптовалютами, работающая в Termux на Android-смартфонах.

**Ключевые особенности:**
- 🏗️ Модульная архитектура с плагинами
- 🌐 Веб-интерфейс (React + Vite)
- ⚡ Realtime данные через WebSocket
- 🔌 Плагины для бирж и стратегий
- 📱 Оптимизировано для мобильных устройств

---

## 🎯 Принципы разработки

### 1. Архитектурные принципы

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React)                        │
│  Dashboard | Positions | Orders | Strategies | Settings     │
└─────────────────────────────────────────────────────────────┘
                            ↕ WebSocket/REST
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Plugins   │  │    Core     │  │      Services       │  │
│  │  Exchange   │  │   Config    │  │   Order Manager     │  │
│  │  Strategy   │  │   Events    │  │   Position Manager  │  │
│  │  Notifier   │  │    Logger   │  │   Data Service      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                      DATA LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   SQLite    │  │   Cache     │  │    External APIs    │  │
│  │  (Models)   │  │  (Redis?)   │  │  (Binance, Bybit)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2. Правила кода

#### Python Backend
```python
# ✅ ДЕЛАТЬ:
# - Использовать type hints
# - Следовать PEPS 8, 257
# - Использовать asyncio для I/O операций
# - Писать unit-тесты для новой логики
# - Логировать через logging.getLogger(__name__)
# - Обрабатывать ошибки явно

# ❌ НЕ ДЕЛАТЬ:
# - Избегать глобальных переменных
# - Не блокировать event loop (time.sleep → asyncio.sleep)
# - Не хранить секреты в коде (только .env)
```

#### TypeScript Frontend
```typescript
// ✅ ДЕЛАТЬ:
// - Использовать TypeScript строго (noImplicitAny)
// - Функциональные компоненты + hooks
// - Типизировать props и state
// - Разделять логику (custom hooks)

// ❌ НЕ ДЕЛАТЬ:
// - Избегать any (использовать unknown)
// - Не мутировать state напрямую
```

### 3. Структура проекта

```
crypto-trader/
├── backend/                    # Python FastAPI сервер
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # Точка входа FastAPI
│   │   ├── config.py          # Конфигурация
│   │   ├── logger.py          # Логирование
│   │   ├── database.py        # SQLite подключение
│   │   │
│   │   ├── core/              # Ядро
│   │   │   ├── __init__.py
│   │   │   ├── events.py      # Event Bus
│   │   │   ├── exceptions.py  # Исключения
│   │   │   └── types.py       # Общие типы
│   │   │
│   │   ├── plugins/           # Система плагинов
│   │   │   ├── __init__.py
│   │   │   ├── base.py        # Базовые классы
│   │   │   ├── manager.py     # Менеджер плагинов
│   │   │   ├── exchange.py    # Базовый класс Exchange
│   │   │   ├── strategy.py    # Базовый класс Strategy
│   │   │   └── notifier.py    # Базовый класс Notifier
│   │   │
│   │   ├── exchanges/         # Плагины бирж
│   │   │   ├── __init__.py
│   │   │   ├── binance.py
│   │   │   ├── bybit.py
│   │   │   └── okx.py
│   │   │
│   │   ├── strategies/        # Плагины стратегий
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── rsi.py
│   │   │   ├── macd.py
│   │   │   └── crossover.py
│   │   │
│   │   ├── indicators/        # Технические индикаторы
│   │   │   ├── __init__.py
│   │   │   ├── sma.py
│   │   │   ├── ema.py
│   │   │   ├── rsi.py
│   │   │   └── macd.py
│   │   │
│   │   ├── models/            # SQLAlchemy модели
│   │   │   ├── __init__.py
│   │   │   ├── candle.py
│   │   │   ├── order.py
│   │   │   ├── position.py
│   │   │   └── trade.py
│   │   │
│   │   ├── services/          # Бизнес-логика
│   │   │   ├── __init__.py
│   │   │   ├── order_manager.py
│   │   │   ├── position_manager.py
│   │   │   ├── data_service.py
│   │   │   ├── risk_manager.py
│   │   │   └── backtester.py
│   │   │
│   │   ├── api/               # REST API роуты
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── config.py
│   │   │   ├── orders.py
│   │   │   ├── positions.py
│   │   │   └── strategies.py
│   │   │
│   │   └── websocket/         # WebSocket handlers
│   │       ├── __init__.py
│   │       ├── manager.py
│   │       └── streams.py
│   │
│   ├── tests/                 # Тесты
│   │   ├── conftest.py
│   │   ├── test_*.py
│   │   └── fixtures/
│   │
│   ├── requirements.txt       # Зависимости Python
│   └── pyproject.toml         # Конфигурация проекта
│
├── frontend/                   # React + Vite UI
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── vite-env.d.ts
│   │   │
│   │   ├── components/        # UI компоненты
│   │   │   ├── ui/           # Базовые компоненты
│   │   │   ├── layout/       # Layout компоненты
│   │   │   └── charts/       # Графики
│   │   │
│   │   ├── pages/            # Страницы
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Positions.tsx
│   │   │   ├── Orders.tsx
│   │   │   ├── Strategies.tsx
│   │   │   └── Settings.tsx
│   │   │
│   │   ├── hooks/            # Custom hooks
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useOrders.ts
│   │   │   └── usePositions.ts
│   │   │
│   │   ├── services/         # API клиенты
│   │   │   ├── api.ts
│   │   │   └── websocket.ts
│   │   │
│   │   ├── store/            # State management
│   │   │   ├── index.ts
│   │   │   └── slices/
│   │   │
│   │   ├── types/            # TypeScript типы
│   │   │   └── index.ts
│   │   │
│   │   └── utils/            # Утилиты
│   │       └── format.ts
│   │
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── scripts/                   # Скрипты установки/запуска
│   ├── install.sh
│   ├── start.sh
│   └── update.sh
│
├── docs/                      # Документация
│   ├── API.md
│   ├── STRATEGIES.md
│   └── EXCHANGES.md
│
├── .env.example              # Шаблон переменных окружения
├── config.yaml.example       # Шаблон конфигурации
├── .gitignore
├── README.md
├── ROADMAP.md
├── AGENT.md                  # Этот файл
├── ARCHITECTURE.md
├── CONTRIBUTING.md
└── DECISIONS.md
```

---

## 🔧 Инструменты разработки

### Backend (Python)

```bash
# Установка зависимостей
pip install -r backend/requirements.txt

# Запуск сервера разработки
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Тесты
pytest backend/tests/ -v --cov=app

# Линтинг
ruff check backend/app/
black backend/app/
mypy backend/app/

# Форматирование
black backend/app/
```

### Frontend (TypeScript)

```bash
cd frontend

# Установка зависимостей
npm install

# Запуск разработки
npm run dev

# Сборка для продакшена
npm run build

# Деплой на GitHub Pages
npm run deploy

# Линтинг
npm run lint
```

---

## 📝 Conventional Commits

Использовать формат [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Типы:**
- `feat:` новая функция
- `fix:` исправление бага
- `docs:` документация
- `style:` форматирование
- `refactor:` рефакторинг
- `test:` тесты
- `chore:` обслуживание

**Примеры:**
```bash
git commit -m "feat(exchange): добавить поддержку Binance API"
git commit -m "fix(strategy): исправить расчёт RSI при нулевых значениях"
git commit -m "docs: обновить README.md с инструкциями установки"
```

---

## 🧪 Тестирование

### Backend тесты

```python
# backend/tests/test_rsi.py
import pytest
from app.indicators.rsi import RSI

def test_rsi_calculation():
    rsi = RSI(period=14)
    prices = [44, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08]
    result = rsi.calculate(prices)
    assert 0 <= result <= 100
```

### Frontend тесты

```typescript
// frontend/src/components/__tests__/OrderBook.test.tsx
import { render, screen } from '@testing-library/react'
import { OrderBook } from '../OrderBook'

test('displays order book data', () => {
  render(<OrderBook orders={mockOrders} />)
  expect(screen.getByText('Buy')).toBeInTheDocument()
})
```

---

## 🔐 Безопасность

### Никогда не коммитить:
- ❌ API ключи
- ❌ Секретные токены
- ❌ Пароли
- ❌ Личные данные

### Использовать:
- ✅ `.env` для секретов
- ✅ `.env.example` без значений
- ✅ Валидацию входных данных
- ✅ Rate limiting для API

---

## 🚀 Деплой

### Backend (Termux)

```bash
# 1. Клонирование
git clone https://github.com/JeBance/crypto-trader.git
cd crypto-trader

# 2. Установка
bash scripts/install.sh

# 3. Конфигурация
cp .env.example .env
# Редактировать .env

# 4. Запуск
bash scripts/start.sh
```

### Frontend (GitHub Pages)

```bash
cd frontend
npm run build
npm run deploy
```

---

## 🐛 Отладка

### Backend
```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Frontend
```typescript
console.log('Debug:', data)
console.error('Error:', error)
// Использовать React DevTools
```

---

## 📚 Полезные ссылки

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [CCXT Documentation](https://docs.ccxt.com/)
- [Termux Wiki](https://wiki.termux.com/)

---

## ❓ Частые вопросы

**Q: Как добавить новую биржу?**
A: Создать класс в `backend/app/exchanges/`, унаследовать от `ExchangePlugin`, реализовать методы.

**Q: Как создать новую стратегию?**
A: Создать класс в `backend/app/strategies/`, унаследовать от `StrategyPlugin`, реализовать `generate_signal()`.

**Q: Как изменить порт сервера?**
A: Изменить `PORT` в `.env` или передать при запуске: `uvicorn app.main:app --port 8080`.

**Q: Как обновить frontend на GitHub Pages?**
A: Запустить `npm run deploy` в папке `frontend/`.

---

*Последнее обновление: 22 февраля 2026*
