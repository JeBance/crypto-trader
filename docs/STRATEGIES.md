# 📊 Trading Strategies — Документация

Полное описание торговых стратегий Crypto Trader.

---

## 🎯 Обзор

Crypto Trader поддерживает плагины стратегий. Каждая стратегия:
- Анализирует рыночные данные (свечи)
- Генерирует торговые сигналы (BUY/SELL)
- Имеет настраиваемые параметры
- Работает независимо через Strategy Executor

---

## 📈 Доступные стратегии

### 1. RSI Strategy

**Файл:** `app/strategies/rsi.py`

**Описание:**
Стратегия на основе индикатора RSI (Relative Strength Index). Генерирует сигналы при достижении перекупленности/перепроданности.

**Сигналы:**
- 🟢 **BUY**: RSI пересекает ниже уровня oversold (30)
- 🔴 **SELL**: RSI пересекает выше уровня overbought (70)

**Параметры:**
| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `period` | Период RSI | 14 |
| `oversold` | Уровень перепроданности | 30 |
| `overbought` | Уровень перекупленности | 70 |

**Пример конфигурации:**
```yaml
strategies:
  rsi:
    enabled: true
    parameters:
      period: 14
      oversold: 30
      overbought: 70
    symbols:
      - BTCUSDT
    timeframe: 1h
```

**Когда использовать:**
- ✅ Флэт (боковое движение)
- ✅ Хорошо работает на ranges
- ❌ Избегать при сильном тренде

---

### 2. Crossover Strategy (SMA/EMA)

**Файл:** `app/strategies/crossover.py`

**Описание:**
Стратегия пересечения скользящих средних. Использует быструю и медленную MA для генерации сигналов.

**Сигналы:**
- 🟢 **BUY (Golden Cross)**: Быстрая MA пересекает выше медленной
- 🔴 **SELL (Death Cross)**: Быстрая MA пересекает ниже медленной

**Параметры:**
| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `fast_period` | Период быстрой MA | 9 |
| `slow_period` | Период медленной MA | 21 |
| `ma_type` | Тип MA (sma/ema) | ema |

**Пример конфигурации:**
```yaml
strategies:
  crossover:
    enabled: true
    parameters:
      fast_period: 9
      slow_period: 21
      ma_type: ema
    symbols:
      - BTCUSDT
    timeframe: 4h
```

**Когда использовать:**
- ✅ Трендовый рынок
- ✅ Долгосрочные стратегии
- ❌ Избегать при флэте (много ложных сигналов)

**Популярные настройки:**
| Стиль | Fast | Slow | Type |
|-------|------|------|------|
| Scalping | 5 | 13 | EMA |
| Day Trading | 9 | 21 | EMA |
| Swing Trading | 20 | 50 | SMA |
| Long Term | 50 | 200 | SMA |

---

### 3. MACD Strategy

**Файл:** `app/strategies/macd.py`

**Описание:**
Стратегия на основе индикатора MACD (Moving Average Convergence Divergence). Генерирует сигналы при пересечении MACD линии и сигнальной линии.

**Сигналы:**
- 🟢 **BUY**: MACD пересекает выше Signal линии
- 🔴 **SELL**: MACD пересекает ниже Signal линии

**Параметры:**
| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `fast_period` | Период быстрой EMA | 12 |
| `slow_period` | Период медленной EMA | 26 |
| `signal_period` | Период сигнальной линии | 9 |

**Пример конфигурации:**
```yaml
strategies:
  macd:
    enabled: true
    parameters:
      fast_period: 12
      slow_period: 26
      signal_period: 9
    symbols:
      - BTCUSDT
    timeframe: 1d
```

**Когда использовать:**
- ✅ Трендовый рынок
- ✅ Подтверждение тренда
- ✅ Среднесрочная торговля

---

## 🔧 Управление стратегиями

### Через API

#### Получить все стратегии
```bash
curl http://localhost:8000/api/strategies
```

#### Получить стратегию по имени
```bash
curl http://localhost:8000/api/strategies/rsi
```

#### Активировать стратегию
```bash
curl -X POST http://localhost:8000/api/strategies/rsi/activate \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

#### Деактивировать стратегию
```bash
curl -X POST http://localhost:8000/api/strategies/rsi/deactivate
```

#### Обновить параметры
```bash
curl -X PUT http://localhost:8000/api/strategies/rsi/parameters \
  -H "Content-Type: application/json" \
  -d '{
    "period": 14,
    "oversold": 25,
    "overbought": 75
  }'
```

### Через UI

1. Откройте `http://localhost:3000/strategies`
2. Найдите нужную стратегию
3. Используйте toggle switch для включения/выключения
4. Настройте параметры (если доступно)

---

## 📊 Сила сигнала

Каждая стратегия рассчитывает силу сигнала (0.5 - 1.0):

| Сила | Значение | Описание |
|------|----------|----------|
| 0.5 - 0.6 | Слабый | Минимальная уверенность |
| 0.6 - 0.7 | Средний | Умеренная уверенность |
| 0.7 - 0.8 | Сильный | Высокая уверенность |
| 0.8 - 1.0 | Очень сильный | Максимальная уверенность |

**Факторы влияния:**
- RSI: отклонение от порога
- Crossover: дивергенция MA
- MACD: гистограмма и дивергенция

---

## 🧪 Бэктестинг стратегий

Перед использованием на реальных данных протестируйте стратегию:

```python
from app.services.backtester import BacktestEngine, BacktestConfig
from app.strategies.rsi import RSIStrategy

# Настройка
engine = BacktestEngine(BacktestConfig(
    initial_capital=10000,
    commission_percent=0.1,
))

# Запуск
strategy = RSIStrategy()
result = await engine.run(strategy, candles, "BTCUSDT")

# Результаты
print(f"Return: {result.total_return}%")
print(f"Win Rate: {result.win_rate}%")
print(f"Max Drawdown: {result.max_drawdown}%")
```

---

## 🎓 Советы по использованию

### 1. Начните с Paper Trading

```bash
# В .env
TRADING_MODE=paper
```

Тестируйте стратегии без риска потери средств.

### 2. Используйте несколько стратегий

Диверсифицируйте риски:
- RSI для флэта
- Crossover для тренда
- MACD для подтверждения

### 3. Настройте Risk Management

```bash
# В .env
MAX_POSITION_SIZE_PERCENT=10
STOP_LOSS_PERCENT=2
TAKE_PROFIT_PERCENT=4
DAILY_LOSS_LIMIT_PERCENT=5
```

### 4. Мониторьте производительность

Проверяйте статистику:
- Win Rate (% прибыльных сделок)
- Profit Factor (прибыль/убыток)
- Max Drawdown (макс. просадка)

### 5. Адаптируйте параметры

Подбирайте параметры под:
- Конкретный актив (BTC, ETH, и т.д.)
- Таймфрейм (1h, 4h, 1d)
- Рыночные условия (тренд/флэт)

---

## 📚 Дополнительные ресурсы

- [ARCHITECTURE.md](ARCHITECTURE.md) — Архитектура стратегий
- [API.md](API.md) — API для управления стратегиями
- [USER_GUIDE.md](USER_GUIDE.md) — Руководство пользователя

---

*Last updated: 22 февраля 2026*
