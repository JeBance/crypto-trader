# 📋 DECISIONS.md — Архитектурные решения (ADR)

Документ содержит принятые архитектурные решения (Architecture Decision Records).

---

## 📖 Что такое ADR

**ADR (Architecture Decision Record)** — документ, описывающий важное архитектурное решение, его контекст и последствия.

Формат:
- **Статус:** Предложено / Принято / Устарело / Заменено
- **Контекст:** Что привело к решению
- **Решение:** Что было решено
- **Последствия:** Плюсы, минусы, ограничения

---

## ADR-001: Выбор стека технологий

**Статус:** Принято  
**Дата:** 22 февраля 2026

### Контекст

Требуется создать торговую систему для запуска на Android в Termux с веб-интерфейсом.

Ограничения:
- Ограниченные ресурсы (RAM 1-4GB, CPU 4-8 ядер)
- Отсутствие root-прав
- Работа через мобильный интернет
- Необходимость realtime-обновлений

### Рассмотренные варианты

#### Backend

| Вариант | Плюсы | Минусы |
|---------|-------|--------|
| Python + FastAPI | Быстрая разработка, богатые библиотеки | Медленнее Go/Node.js |
| Node.js + Express | Быстрый, асинхронный | Меньше библиотек для трейдинга |
| Go + Gin | Очень быстрый, статический бинарник | Сложнее разработка, меньше библиотек |
| Rust + Actix | Самый быстрый, безопасный | Дольше разработка, сложный язык |

#### Frontend

| Вариант | Плюсы | Минусы |
|---------|-------|--------|
| React + Vite | Популярный, богатая экосистема | Больше размер бандла |
| Vue + Vite | Проще React | Меньше экосистема |
| Svelte | Меньше размер | Меньше сообщество |
| Vanilla JS | Минимальный размер | Сложнее поддержка |

### Решение

**Backend:** Python 3.10+ + FastAPI
- Богатые библиотеки для трейдинга (ccxt, ta-lib, pandas)
- Быстрая разработка
- Async/await для I/O операций
- Автоматическая документация (OpenAPI)

**Frontend:** React 18 + TypeScript + Vite
- Популярный фреймворк
- Богатая экосистема компонентов
- TypeScript для типобезопасности
- Vite для быстрой сборки

### Последствия

**Положительные:**
- Быстрая разработка MVP
- Много готовых библиотек
- Легко найти разработчиков

**Отрицательные:**
- Больше потребление памяти (Python)
- Больше размер бандла (React)

**Компенсации:**
- LRU кэширование для оптимизации памяти
- Code splitting для уменьшения бандла

---

## ADR-002: Модульная архитектура с плагинами

**Статус:** Принято  
**Дата:** 22 февраля 2026

### Контекст

Требуется гибкая архитектура для поддержки:
- Множественных бирж (Binance, Bybit, OKX, ...)
- Множественных стратегий (RSI, MACD, ...)
- Множественных нотификаторов (Telegram, Email, ...)

### Рассмотренные варианты

| Вариант | Плюсы | Минусы |
|---------|-------|--------|
| Монолит с условиями | Проще реализация | Сложно расширять |
| Микросервисы | Изоляция, масштабируемость | Сложность, overhead |
| Plugin architecture | Гибкость, расширяемость | Сложнее тестирование |
| Event-driven | Loose coupling | Сложнее отладка |

### Решение

**Plugin Architecture + Event Bus**

```
┌─────────────────────────────────────────┐
│           Application Core              │
│  ┌─────────────────────────────────┐    │
│  │         Plugin Manager          │    │
│  └─────────────────────────────────┘    │
│         │              │                │
│         ▼              ▼                │
│  ┌────────────┐  ┌────────────┐         │
│  │  Exchange  │  │  Strategy  │         │
│  │  Plugins   │  │  Plugins   │         │
│  └────────────┘  └────────────┘         │
└─────────────────────────────────────────┘
```

**Базовые классы:**
```python
class ExchangePlugin(ABC):
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker: ...
    
    @abstractmethod
    async def create_order(self, order: OrderRequest) -> Order: ...

class StrategyPlugin(ABC):
    @abstractmethod
    async def on_candle(self, candle: Candle) -> Optional[Signal]: ...

class NotifierPlugin(ABC):
    @abstractmethod
    async def send(self, message: str, level: str = "info") -> None: ...
```

### Последствия

**Положительные:**
- Легко добавить новую биржу/стратегию
- Изоляция кода
- Тестируемость отдельных компонентов

**Отрицательные:**
- Сложнее начальная настройка
- overhead на абстракции

---

## ADR-003: Выбор базы данных

**Статус:** Принято  
**Дата:** 22 февраля 2026

### Контекст

Требуется хранение:
- Истории свечей
- Ордеров и сделок
- Позиций
- Настроек стратегий

Ограничения:
- Запуск на Android в Termux
- Локальное хранение
- Минимальная настройка

### Рассмотренные варианты

| Вариант | Плюсы | Минусы |
|---------|-------|--------|
| SQLite | Встроена, нет настройки | Нет concurrent writes |
| PostgreSQL | Мощная, concurrent | Требует сервер |
| MongoDB | Гибкая схема | Требует сервер |
| Redis | Быстрая, in-memory | Требует сервер, volatile |
| Files (JSON/CSV) | Проще всего | Нет query, медленно |

### Решение

**SQLite + SQLAlchemy**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///crypto_trader.db")
SessionLocal = sessionmaker(bind=engine)
```

**Модели:**
- Candle (OHLCV данные)
- Order (ордера)
- Position (позиции)
- Trade (исполненные сделки)

### Последствия

**Положительные:**
- Нет отдельного сервера
- Встроена в Python
- ACID транзакции
- SQL запросы

**Отрицательные:**
- Нет concurrent writes (но для одного пользователя OK)
- Ограничения масштабируемости

**Компенсации:**
- WAL mode для лучшей производительности
- Индексы на часто используемых полях

---

## ADR-004: Realtime коммуникация (WebSocket)

**Статус:** Принято  
**Дата:** 22 февраля 2026

### Контекст

Требуется realtime обновление:
- Цен и свечей
- Статуса ордеров
- PnL позиций
- Сигналов стратегий

### Рассмотренные варианты

| Вариант | Плюсы | Минусы |
|---------|-------|--------|
| WebSocket | Full-duplex, low latency | Сложнее HTTP |
| Server-Sent Events | Проще WebSocket | Только server→client |
| Long Polling | Проще всего | High latency, overhead |
| GraphQL Subscriptions | Мощно | Сложнее, overhead |

### Решение

**WebSocket + FastAPI**

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"type": "price", "data": {...}})
```

**Клиент (React):**
```typescript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Update state
};
```

### Последствия

**Положительные:**
- Low latency (<100ms)
- Full-duplex коммуникация
- Efficient (одно соединение)

**Отрицательные:**
- Сложнее отладка
- Нужно handle reconnect

**Компенсации:**
- Автоматический reconnect в клиенте
- Heartbeat для keep-alive

---

## ADR-005: Разделение Backend/Frontend

**Статус:** Принято  
**Дата:** 22 февраля 2026

### Контекст

Требуется:
- Backend работает локально в Termux
- Frontend доступен через браузер
- Frontend деплоится на GitHub Pages

### Решение

**Полное разделение:**

```
┌─────────────────────┐         ┌─────────────────────┐
│   Frontend (SPA)    │         │   Backend (API)     │
│   React + Vite      │◀───────▶│   FastAPI           │
│   GitHub Pages      │  HTTP/  │   Termux            │
│                     │   WS    │                     │
└─────────────────────┘         └─────────────────────┘
```

**API контракты:**
- REST API для CRUD операций
- WebSocket для realtime данных
- OpenAPI спецификация для документации

### Последствия

**Положительные:**
- Независимая разработка
- Frontend может работать с любого хоста
- Легко заменить frontend/backend

**Отрицательные:**
- CORS настройка
- Две кодовые базы

---

## ADR-006: Paper Trading режим

**Статус:** Принято  
**Дата:** 22 февраля 2026

### Контекст

Пользователи должны тестировать стратегии без риска потери реальных средств.

### Решение

**Paper Trading как обёртка над Exchange:**

```python
class PaperExchange(ExchangePlugin):
    """Симуляция биржи для тестирования"""
    
    def __init__(self, real_exchange: ExchangePlugin, initial_balance: float):
        self.real_exchange = real_exchange
        self.balance = initial_balance
        self.positions = {}
        self.orders = {}
    
    async def create_order(self, order: OrderRequest) -> Order:
        # Симуляция ордера на реальных данных
        # Не отправлять на реальную биржу
        pass
```

### Последствия

**Положительные:**
- Безопасное тестирование
- Реальные рыночные данные
- Легко переключаться между paper/live

**Отрицательные:**
- Дублирование логики
- Может отличаться от реального исполнения

---

## ADR-007: Конфигурация через .env + YAML

**Статус:** Принято  
**Дата:** 22 февраля 2026

### Контекст

Требуется хранение:
- Секретов (API ключи, токены)
- Настроек (параметры стратегий, риски)

### Решение

**.env для секретов:**
```bash
BINANCE_API_KEY=xxx
BINANCE_API_SECRET=yyy
TELEGRAM_BOT_TOKEN=zzz
```

**config.yaml для настроек:**
```yaml
trading:
  mode: paper  # paper, live
  exchanges:
    - binance
  strategies:
    - name: rsi
      enabled: true
      parameters:
        period: 14
        oversold: 30
        overbought: 70

risk:
  max_position_size: 0.1  # 10% от депозита
  stop_loss: 0.02  # 2%
  daily_loss_limit: 0.05  # 5%
```

### Последствия

**Положительные:**
- Секреты отдельно от настроек
- Человекочитаемый формат
- Легко версионировать (без секретов)

**Отрицательные:**
- Два файла конфигурации

---

## ADR-008: GitHub Pages для Frontend

**Статус:** Принято  
**Дата:** 22 февраля 2026

### Контекст

Frontend должен быть доступен:
- Локально (разработка)
- На GitHub Pages (продакшен)

### Решение

**Vite + gh-pages:**

```json
// package.json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "deploy": "npm run build && gh-pages -d dist"
  },
  "homepage": "https://jebance.github.io/crypto-trader/"
}
```

**API URL конфигурируется:**
```typescript
// development
const API_URL = 'http://localhost:8000';

// production
const API_URL = 'http://<device-ip>:8000';
```

### Последствия

**Положительные:**
- Бесплатный хостинг
- Автоматический деплой
- HTTPS из коробки

**Отрицательные:**
- Статический сайт (нет SSR)
- API URL нужно настраивать

---

## ADR-009: Логирование и мониторинг

**Статус:** Принято  
**Дата:** 22 февраля 2026

### Контекст

Требуется:
- Отладка проблем
- Аудит действий
- Мониторинг состояния

### Решение

**Структурированное логирование:**

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Получены свечи: %s", symbol)
logger.info("Ордер создан: %s", order_id)
logger.warning("Близко к лимиту убытка: %s%%", loss_percent)
logger.error("Ошибка биржи: %s", error)
```

**Формат логов:**
```
2026-02-22 10:30:15.123 | INFO     | app.strategy.rsi:on_candle:45 - RSI сигнал: BUY (RSI=28.5)
```

**Ротация логов:**
```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "logs/trader.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

### Последствия

**Положительные:**
- Легко отладить проблемы
- Аудит всех действий
- Ограниченный размер логов

**Отрицательные:**
- overhead на запись логов

---

## ADR-010: Обработка ошибок и retry logic

**Статус:** Принято  
**Дата:** 22 февраля 2026

### Контекст

API бирж могут:
- Возвращать ошибки
- Иметь rate limits
- Быть недоступными

### Решение

**Retry с exponential backoff:**

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=30)
)
async def get_ticker(self, symbol: str) -> Ticker:
    response = await self.session.get(...)
    response.raise_for_status()
    return Ticker(**response.json())
```

**Rate limiting:**
```python
from aiolimiter import AsyncLimiter

limiter = AsyncLimiter(max_rate=10, time_period=1)  # 10 запросов в секунду

async with limiter:
    await api_call()
```

### Последствия

**Положительные:**
- Устойчивость к временным ошибкам
- Соблюдение rate limits

**Отрицательные:**
- Задержки при retry
- Сложнее отладка

---

## 📝 Новые ADR

Для добавления нового ADR:

1. Создайте секцию с номером (ADR-XXX)
2. Заполните шаблон:
   - Статус
   - Дата
   - Контекст
   - Рассмотренные варианты
   - Решение
   - Последствия

---

*Последнее обновление: 22 февраля 2026*
