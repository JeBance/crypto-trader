# 📊 Data Collection Guide

Руководство по сбору и хранению рыночных данных.

---

## 🎯 Обзор

Crypto Trader теперь автоматически собирает и сохраняет исторические рыночные данные с бирж. Данные сохраняются в базу данных SQLite и **никогда не удаляются автоматически**.

### Возможности

- ✅ **Автоматический сбор свечей** — непрерывный сбор OHLCV данных
- ✅ **Умная загрузка** — загрузка из БД с автоматическим заполнением пробелов
- ✅ **Сохранение истории** — все данные сохраняются навсегда
- ✅ **Backfill** — автоматическая догрузка истории при возобновлении мониторинга
- ✅ **API управление** — REST API для управления мониторингом
- ✅ **Мониторинг** — логирование и статистика сбора данных

---

## 📁 Структура данных

### Таблицы базы данных

```
crypto_trader.db
├── monitored_pairs          # Пары, выбранные пользователем
│   ├── exchange            # Биржа (binance, bybit)
│   ├── symbol              # Торговая пара (BTCUSDT)
│   ├── timeframes          # Таймфреймы (1h,4h,1d)
│   ├── is_active           # Активен ли мониторинг
│   └── last_data_at        # Время последнего сбора
│
├── candles                  # Свечи (OHLCV)
│   ├── exchange, symbol, timeframe
│   ├── timestamp, open, high, low, close, volume
│   └── уникальность: (exchange, symbol, timeframe, timestamp)
│
├── tickers                  # 24h статистика
│   ├── exchange, symbol, timestamp
│   └── last_price, volume_24h, change_24h, ...
│
├── trades                   # Последние сделки
│   ├── exchange, symbol, trade_id
│   └── price, quantity, side, fee
│
├── order_book_snapshots     # Снимки стакана цен
│   ├── exchange, symbol, timestamp
│   └── bids, asks, spread, depth
│
└── data_collection_logs     # Логи сбора данных
    ├── exchange, symbol, data_type
    ├── status, records_collected
    └── error_message
```

---

## 🚀 Быстрый старт

### 1. Добавить пару в мониторинг

```bash
curl -X POST http://localhost:8000/api/market-data/monitored-pairs \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "timeframes": ["1h", "4h", "1d"],
    "is_active": true
  }'
```

### 2. Проверить статус

```bash
curl http://localhost:8000/api/market-data/stats
```

### 3. Получить исторические данные

```bash
curl "http://localhost:8000/api/market-data/candles/BTCUSDT?timeframe=1h&limit=100"
```

---

## 📖 API Endpoints

### Monitored Pairs

#### GET /api/market-data/monitored-pairs

Получить список всех monitored пар.

**Параметры:**
- `active_only` (bool) — вернуть только активные пары

**Ответ:**
```json
[
  {
    "id": 1,
    "exchange": "binance",
    "symbol": "BTCUSDT",
    "timeframes": ["1h", "4h", "1d"],
    "is_active": true,
    "created_at": "2026-02-23T10:00:00Z",
    "last_data_at": "2026-02-23T14:30:00Z"
  }
]
```

#### POST /api/market-data/monitored-pairs

Добавить пару в мониторинг.

**Тело запроса:**
```json
{
  "symbol": "BTCUSDT",
  "timeframes": ["1h", "4h", "1d"],
  "is_active": true
}
```

#### DELETE /api/market-data/monitored-pairs/{symbol}

Удалить пару из мониторинга.

⚠️ **Важно:** Исторические данные НЕ удаляются! Только останавливается будущий сбор.

#### POST /api/market-data/monitored-pairs/{symbol}/resume

Возобновить мониторинг для ранее добавленной пары.

🔄 Автоматически запускается backfill пропущенных данных.

---

### Candle Data

#### GET /api/market-data/candles/{symbol}

Получить исторические свечи.

**Параметры:**
- `timeframe` (required) — таймфрейм (1h, 4h, 1d, ...)
- `limit` (optional) — количество свечей (1-1000, по умолчанию 100)

**Ответ:**
```json
[
  {
    "timestamp": "2026-02-23T14:00:00Z",
    "open": 52000.0,
    "high": 52500.0,
    "low": 51800.0,
    "close": 52300.0,
    "volume": 1234.56
  }
]
```

#### GET /api/market-data/candles/{symbol}/count

Получить общее количество свечей в БД.

---

### Statistics

#### GET /api/market-data/stats

Получить статистику сбора данных.

**Ответ:**
```json
{
  "exchange": "binance",
  "total_monitored_pairs": 5,
  "active_pairs": 3,
  "total_candles": 50000,
  "date_range_from": "2026-01-01T00:00:00Z",
  "date_range_to": "2026-02-23T14:00:00Z",
  "last_collection": "2026-02-23T14:30:00Z"
}
```

---

### Collection Logs

#### GET /api/market-data/logs

Получить логи сбора данных.

**Параметры:**
- `limit` (optional) — количество записей (1-500)
- `symbol` (optional) — фильтр по паре
- `status` (optional) — фильтр по статусу (success/error)

---

## 🔄 Как работает сбор данных

### 1. Пользователь добавляет пару

```
POST /api/market-data/monitored-pairs
→ Пара сохраняется в БД
→ CandleCollector начинает сбор
```

### 2. Непрерывный сбор

```
CandleCollector (каждые 10 секунд)
  ↓
Для каждой активной пары:
  - Получить последнюю свечу с биржи
  - Проверить, есть ли в БД
  - Если нет → сохранить
  - Если есть → проверить обновления
```

### 3. Умная загрузка

```
Запрос свечей через API
  ↓
1. Проверка кэша (LRU)
2. Загрузка из БД
3. Если не хватает → дозагрузка с биржи
4. Сохранение в БД
5. Возврат данных
```

### 4. Backfill при возобновлении

```
Возобновление мониторинга
  ↓
1. Получить последнюю свечу в БД
2. Получить текущую свечу с биржи
3. Обнаружить пробелы
4. Заполнить пробелы через API биржи
5. Сохранить в БД
```

---

## ⚙️ Конфигурация

### Интервалы сбора

| Данные | Интервал | Описание |
|--------|----------|----------|
| Свечи | 10 секунд | Проверка новых свечей |
| Тикеры | 60 секунд | 24h статистика |
| Сделки | 30 секунд | Последние трейды |

### Таймфреймы

Поддерживаемые таймфреймы:
- Минутные: `1m`, `5m`, `15m`, `30m`
- Часовые: `1h`, `2h`, `4h`, `6h`, `12h`
- Дневные/Недельные: `1d`, `1w`, `1M`

---

## 📊 Примеры использования

### Python пример

```python
import requests

# Добавить пару в мониторинг
response = requests.post(
    "http://localhost:8000/api/market-data/monitored-pairs",
    json={
        "symbol": "BTCUSDT",
        "timeframes": ["1h", "4h"],
        "is_active": True
    }
)
print(response.json())

# Получить статистику
response = requests.get("http://localhost:8000/api/market-data/stats")
stats = response.json()
print(f"Total candles: {stats['total_candles']}")

# Получить свечи
response = requests.get(
    "http://localhost:8000/api/market-data/candles/BTCUSDT",
    params={"timeframe": "1h", "limit": 100}
)
candles = response.json()
print(f"Last candle: {candles[-1]}")
```

### Frontend интеграция

```typescript
// React hook для получения свечей
function useCandles(symbol: string, timeframe: string, limit = 100) {
  const [candles, setCandles] = useState([]);
  
  useEffect(() => {
    fetch(`/api/market-data/candles/${symbol}?timeframe=${timeframe}&limit=${limit}`)
      .then(res => res.json())
      .then(data => setCandles(data));
  }, [symbol, timeframe, limit]);
  
  return candles;
}
```

---

## 🔍 Мониторинг и отладка

### Проверка статуса

```bash
# Статистика
curl http://localhost:8000/api/market-data/stats

# Логи сбора
curl "http://localhost:8000/api/market-data/logs?limit=10"

# Активные пары
curl http://localhost:8000/api/market-data/monitored-pairs?active_only=true
```

### Логи приложения

```
2026-02-23 14:30:15.123 | INFO     | CandleCollector     | Starting CandleCollector...
2026-02-23 14:30:15.456 | INFO     | CandleCollector     | Loaded 5 monitored pairs from database
2026-02-23 14:30:15.789 | INFO     | CandleCollector     | CandleCollector started (interval=10s)
2026-02-23 14:30:25.123 | INFO     | DataCollectionLog   | Saved 1 candles to DB for binance:BTCUSDT
```

---

## ⚠️ Важные заметки

### Сохранение данных

- ✅ Данные **НЕ удаляются** автоматически
- ✅ При остановке мониторинга история сохраняется
- ✅ При возобновлении происходит backfill пробелов

### Производительность

- 📊 LRU кэш для часто запрашиваемых данных
- 📊 Индексы в БД для быстрого поиска
- 📊 Пакетная вставка для эффективности

### Лимиты бирж

| Биржа | Лимит свечей | Лимит запросов |
|-------|--------------|----------------|
| Binance | 1000 за запрос | 1200 weight/min |
| Bybit | 1000 за запрос | 100 requests/s |

---

## 🐛 Troubleshooting

### Проблема: Нет данных в БД

**Решение:**
1. Проверьте, что пара добавлена в мониторинг
2. Проверьте логи на ошибки сбора
3. Убедитесь, что биржа настроена (API ключи)

### Проблема: Медленная загрузка

**Решение:**
1. Проверьте размер БД (`SELECT count(*) FROM candles;`)
2. Увеличьте интервал сбора если высокая нагрузка
3. Проверьте логи на частые ошибки

### Проблема: Пробелы в данных

**Решение:**
1. Возобновите мониторинг пары (запустит backfill)
2. Проверьте логи на ошибки API
3. Убедитесь в стабильном интернет-соединении

---

## 📚 Связанная документация

- [API Documentation](API.md) — Полная REST API документация
- [Architecture](ARCHITECTURE.md) — Архитектура системы
- [Exchanges](EXCHANGES.md) — Поддерживаемые биржи

---

*Последнее обновление: 23 февраля 2026*
