# 🌐 Crypto Trader — Руководство пользователя

Работа с приложением через веб-интерфейс (без терминала).

---

## 🚀 Быстрый старт

### 1. Запуск сервера

```bash
bash run.sh
```

**Всё!** Сервер запустится и создаст `.env` файл автоматически.

### 2. Открыть в браузере

```
http://localhost:8000      # Backend API
http://localhost:8000/docs # API документация (Swagger)
http://localhost:3000      # Frontend UI
```

---

## 📱 Страницы веб-интерфейса

### Dashboard (Главная)

**URL:** `http://localhost:3000`

**Что показывает:**
- 💰 Total Balance — общий баланс
- 📈 Today P&L — прибыль/убыток за день
- 📊 Active Positions — открытые позиции
- 🧠 Active Strategies — активные стратегии
- System Status — статус системы

---

### Positions (Позиции)

**URL:** `http://localhost:3000/positions`

**Функции:**
- Просмотр открытых позиций
- P&L в реальном времени
- Кнопка "Close" для закрытия позиции

---

### Orders (Ордера)

**URL:** `http://localhost:3000/orders`

**Функции:**
- История ордеров
- Фильтр по статусу (All, Open, Filled, Cancelled)
- Фильтр по символу (BTCUSDT, ETHUSDT)
- Кнопка "Cancel" для отмены ордера

---

### Strategies (Стратегии)

**URL:** `http://localhost:3000/strategies`

**Функции:**
- Список доступных стратегий
- Вкл/Выкл стратегии (toggle switch)
- Параметры стратегии
- Символы для торговли
- Таймфрейм

**Как включить стратегию:**
1. Откройте Strategies page
2. Найдите нужную стратегию (например, RSI)
3. Включите toggle switch
4. Настройте параметры (опционально)

---

### Settings (Настройки)

**URL:** `http://localhost:3000/settings`

**Функции:**
- Просмотр конфигурации
- Статус подключения бирж
- Статус Telegram уведомлений
- Настройки рисков

---

## 🔧 Настройка через UI

### Настройка API ключей

API ключи можно добавить двумя способами:

#### Способ 1: Через Settings page (рекомендуется)

1. Откройте `http://localhost:3000/settings`
2. Найдите секцию "Exchanges"
3. Нажмите "Configure" (если доступно)
4. Введите API ключи
5. Нажмите "Save"

#### Способ 2: Через редактирование .env

1. Откройте файл `.env` в корне проекта
2. Добавьте ключи:

```bash
# Binance
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
BINANCE_TESTNET=true

# Bybit
BYBIT_API_KEY=your_bybit_api_key
BYBIT_API_SECRET=your_bybit_api_secret
BYBIT_TESTNET=true
```

3. Перезапустите сервер

---

## 📊 API Документация

### Swagger UI

**URL:** `http://localhost:8000/docs`

**Что можно делать:**
- Просматривать все API endpoints
- Тестировать API прямо из браузера
- Видеть схемы запросов/ответов

### ReDoc

**URL:** `http://localhost:8000/redoc`

**Что можно делать:**
- Читать подробную документацию
- Видеть примеры ответов

---

## 🔍 Проверка статуса

### Health Check

```bash
curl http://localhost:8000/api/health
```

**Ответ:**
```json
{
  "status": "healthy",
  "name": "Crypto Trader",
  "version": "0.2.0",
  "timestamp": "2026-02-22T..."
}
```

### System Status

```bash
curl http://localhost:8000/api/health/status
```

**Ответ:**
```json
{
  "application": {
    "name": "Crypto Trader",
    "version": "0.2.0",
    "environment": "development",
    "trading_mode": "paper"
  },
  "configuration": {
    "fully_configured": false,
    "exchanges": {
      "binance": false,
      "bybit": false
    },
    "telegram": false
  }
}
```

---

## ⚙️ Конфигурация

### Просмотр текущей конфигурации

```bash
curl http://localhost:8000/api/config
```

### Что означают настройки:

| Настройка | Описание | Значение по умолчанию |
|-----------|----------|----------------------|
| `APP_ENV` | Окружение | `development` |
| `APP_DEBUG` | Debug режим | `true` |
| `TRADING_MODE` | Режим торговли | `paper` (демо) |
| `MAX_POSITION_SIZE_PERCENT` | Макс. размер позиции | `10%` |
| `STOP_LOSS_PERCENT` | Стоп-лосс | `2%` |
| `TAKE_PROFIT_PERCENT` | Тейк-профит | `4%` |
| `DAILY_LOSS_LIMIT_PERCENT` | Лимит убытка за день | `5%` |

---

## 🎯 Типовые сценарии

### Сценарий 1: Первый запуск

1. Запустите сервер: `bash run.sh`
2. Откройте браузер: `http://localhost:3000`
3. Проверьте Dashboard — всё должно быть зелёным
4. Перейдите в Settings — проверьте статус конфигурации

### Сценарий 2: Включение стратегии

1. Откройте Strategies: `http://localhost:3000/strategies`
2. Включите RSI стратегию
3. Перейдите на Dashboard
4. Проверьте "Active Strategies" — должно стать 1

### Сценарий 3: Добавление API ключей

1. Получите API ключи на бирже (Binance/Bybit)
2. Откройте Settings: `http://localhost:3000/settings`
3. Добавьте ключи в секции "Exchanges"
4. Сохраните
5. Перезапустите сервер

### Сценарий 4: Проверка логов

1. Откройте терминал
2. Смотрите логи сервера в реальном времени:
   ```bash
   tail -f logs/server.log
   ```

---

## 🛠️ Решение проблем

### Проблема: Сервер не запускается

**Проверьте логи:**
```bash
tail -100 logs/server.log
```

**Частые ошибки:**
- Port 8000 занят → измените PORT в `.env`
- Python не найден → установите Python 3.10+

### Проблема: Frontend не открывается

**Проверьте:**
1. Запущен ли frontend: `npm run dev` в папке `frontend/`
2. Порт 3000 не занят ли

**Решение:**
```bash
cd frontend
npm install
npm run dev
```

### Проблема: "Not configured" в Settings

**Это нормально!** Значит API ключи не добавлены.

**Как исправить:**
1. Добавьте API ключи в `.env`
2. Перезапустите сервер

---

## 📚 Дополнительные ресурсы

### Документация

- [API Documentation](/docs/API.md) — REST API endpoints
- [Self-Healing Server](/docs/SELF_HEALING_SERVER.md) — автономная работа
- [Installation Guide](/docs/INSTALL.md) — подробная установка

### API Endpoints

```
GET  /api/health              # Health check
GET  /api/health/status       # System status
GET  /api/config              # Configuration
GET  /api/orders              # Orders list
GET  /api/positions           # Positions list
GET  /api/strategies          # Strategies list
POST /api/strategies/{name}/activate    # Activate strategy
WS   /ws/stream               # WebSocket for realtime
```

---

## 💡 Советы

1. **Используйте testnet** для тестирования
   - Binance Testnet: https://testnet.binance.vision
   - Bybit Testnet: https://testnet.bybit.com

2. **Проверяйте логи** при проблемах
   ```bash
   tail -f logs/server.log
   ```

3. **Начните с Paper Trading**
   - Убедитесь что `TRADING_MODE=paper` в `.env`

4. **Мониторьте Dashboard**
   - Откройте в браузере и оставьте на экране
   - Все изменения видны в реальном времени

---

*Last updated: 22 февраля 2026*
