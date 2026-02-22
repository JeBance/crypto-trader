# 🔄 Self-Healing Server Guide

Руководство по использованию самовосстанавливающегося сервера с авто-обновлением.

---

## 📖 Обзор

**Self-Healing Server** — это режим запуска приложения с автоматическим:
- Мониторингом состояния сервисов
- Перезапуском при сбоях
- Обновлением из Git репозитория
- Логированием в реальном времени

---

## 🚀 Быстрый старт

### Запуск на Android (Termux)

```bash
# 1. Перейдите в директорию проекта
cd crypto-trader

# 2. Запустите сервер
bash run.sh
```

### Режимы запуска

```bash
# Обычный запуск
bash run.sh

# Debug режим (подробные логи)
bash run.sh --debug

# Без авто-обновления
bash run.sh --no-auto-update

# Комбинированный
bash run.sh --debug --no-auto-update
```

---

## 📊 Что делает сервер

### 1. Supervisor (Монитор сервисов)

```
┌─────────────────────────────────────────┐
│           Supervisor                    │
│  ┌─────────────────────────────────┐    │
│  │  API Service (FastAPI)          │    │
│  │  - Мониторинг процесса          │    │
│  │  - Авто-перезапуск при падении  │    │
│  │  - Чтение логов в реальном времени│   │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**Функции:**
- Запускает FastAPI сервер
- Следит за процессом
- Автоматически перезапускает при выходе
- Ограничивает количество перезапусков (защита от loop)

### 2. Health Monitor (Проверка здоровья)

```
Каждые 30 секунд:
  ├─ Проверка API (/api/health)
  ├─ Если failed → попытка перезапуска
  └─ Если recovered → логирование
```

**Параметры:**
- Интервал проверки: 30 секунд
- Максимум ошибок перед рестартом: 3
- Таймаут проверки: 10 секунд

### 3. Auto Updater (Авто-обновление)

```
Каждые 5 минут:
  ├─ Git fetch origin gh-pages
  ├─ Сравнение коммитов
  ├─ Если новый → git pull
  └─ Перезапуск приложения
```

**Функции:**
- Проверка новых коммитов
- Автоматический pull
- Graceful restart
- Hook скрипты (pre/post restart)

---

## 📋 Вывод в терминале

### Пример логов

```
============================================================
🚀 Crypto Trader - Self-Healing Server
============================================================

[INFO] 2026-02-22 18:00:00 - Using Python: Python 3.10.12
[INFO] 2026-02-22 18:00:00 - Virtual environment found
[INFO] 2026-02-22 18:00:01 - Checking dependencies...
[OK] 2026-02-22 18:00:02 - Dependencies OK

[INFO] 2026-02-22 18:00:02 - Starting Crypto Trader Server...
[INFO] 2026-02-22 18:00:02 - Press Ctrl+C to stop
============================================================

2026-02-22 18:00:03 | INFO     | supervisor        | Starting Supervisor...
2026-02-22 18:00:03 | INFO     | supervisor        | Registered service: api
2026-02-22 18:00:03 | INFO     | supervisor        | Starting service: api
2026-02-22 18:00:04 | INFO     | supervisor        | Service 'api' started with PID 12345
2026-02-22 18:00:04 | INFO     | health_monitor    | Starting Health Monitor (1 checks)
2026-02-22 18:00:04 | INFO     | updater           | Starting Auto-Updater...
2026-02-22 18:00:04 | INFO     | updater           | Current commit: abc12345

# Статус каждые 60 секунд
============================================================
📊 SERVER STATUS
============================================================
Supervisor: ✅ Running
  ✅ api: running (restarts: 0)
Health: ✅ All healthy
Auto-Update: ✅ Enabled (commit: abc12345)
============================================================
```

### При сбое и перезапуске

```
2026-02-22 18:05:00 | WARNING  | supervisor        | Service 'api' exited with code 1
2026-02-22 18:05:00 | INFO     | supervisor        | Restarting service 'api' (attempt 1/10)
2026-02-22 18:05:05 | INFO     | supervisor        | Starting service: api
2026-02-22 18:05:06 | INFO     | supervisor        | Service 'api' started with PID 12346
```

### При авто-обновлении

```
2026-02-22 18:10:00 | INFO     | updater           | Checking for updates...
2026-02-22 18:10:01 | INFO     | updater           | New update available!
2026-02-22 18:10:02 | INFO     | updater           | Pull successful
2026-02-22 18:10:02 | INFO     | updater           | Updated to commit: def67890
2026-02-22 18:10:02 | INFO     | updater           | Triggering application restart...
```

---

## ⚙️ Конфигурация

### Переменные окружения

```bash
# .env файл

# Server settings
HOST=0.0.0.0
PORT=8000

# Auto-update settings
AUTO_UPDATE_INTERVAL=300  # Проверка обновлений (секунды)
AUTO_UPDATE_BRANCH=gh-pages

# Health check settings
HEALTH_CHECK_INTERVAL=30  # Интервал проверки (секунды)
HEALTH_CHECK_TIMEOUT=10   # Таймаут проверки (секунды)
HEALTH_MAX_FAILURES=3     # Максимум ошибок перед рестартом
```

### Настройка в run_server.py

```python
# Изменение параметров
server = Server(
    debug=True,              # Debug режим
    auto_update=False,       # Отключить авто-обновление
)

# Настройка supervisor
supervisor.register_service(
    name="api",
    restart_delay=5,         # Задержка перед рестартом (сек)
    max_restarts=10,         # Максимум рестартов
    restart_window=300,      # Окно для подсчета рестартов (сек)
)

# Настройка updater
updater = AutoUpdater(
    check_interval=300,      # Интервал проверки (сек)
    branch="gh-pages",       # Ветка для отслеживания
)
```

---

## 🔧 Hook скрипты

Можно создать hook скрипты для выполнения кода до/после перезапуска:

```bash
scripts/
├── hook_prerestart.sh    # Выполняется перед перезапуском
└── hook_postrestart.sh   # Выполняется после перезапуска
```

### Пример hook_prerestart.sh

```bash
#!/bin/bash
# Сохранение состояния перед перезапуском

echo "Saving state before restart..."
curl http://localhost:8000/api/positions > /sdcard/positions_backup.json
echo "State saved"
```

### Пример hook_postrestart.sh

```bash
#!/bin/bash
# Отправка уведомления после перезапуска

echo "Sending restart notification..."
# Отправка в Telegram
curl -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d "chat_id=<CHAT_ID>" \
  -d "text=🔄 Server restarted successfully"
```

---

## 📊 Мониторинг

### Проверка статуса

```bash
# Статус сервера
bash run.sh --status

# Вывод:
# [INFO] Server Status:
#   Restart Count: 1
#   Recent Restarts: 1
#   Log File: /path/to/logs/server.log
#   ✅ Server running (PID: 12345)
```

### Просмотр логов

```bash
# Последние 50 строк
tail -50 logs/server.log

# В реальном времени
tail -f logs/server.log

# Поиск ошибок
grep "ERROR" logs/server.log
```

### API статус

```bash
# Health check
curl http://localhost:8000/api/health

# Детальный статус
curl http://localhost:8000/api/health/status
```

---

## 🛠️ Troubleshooting

### Сервер не запускается

```bash
# Проверка Python
python3 --version

# Проверка зависимостей
pip install -r backend/requirements.txt

# Запуск в debug режиме
bash run.sh --debug
```

### Частые перезапуски

```bash
# Посмотреть логи
tail -f logs/server.log

# Проверить exit code
grep "exited with code" logs/server.log

# Временно отключить авто-обновление
bash run.sh --no-auto-update
```

### Проблемы с авто-обновлением

```bash
# Проверка Git
git status
git fetch origin gh-pages

# Ручное обновление
git pull origin gh-pages

# Отключить авто-обновление
bash run.sh --no-auto-update
```

### Увеличение лимита рестартов

Отредактируйте `run_server.py`:

```python
self.supervisor.register_service(
    name="api",
    max_restarts=20,      # Увеличить лимит
    restart_window=600,   # Увеличить окно (10 минут)
)
```

---

## 📱 Запуск на Android (Termux)

### 1. Установка

```bash
# Обновление пакетов
pkg update && pkg upgrade

# Установка зависимостей
pkg install python git curl wget

# Клонирование
git clone https://github.com/JeBance/crypto-trader.git
cd crypto-trader

# Установка Python зависимостей
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### 2. Настройка

```bash
# Копирование конфига
cp .env.example .env

# Редактирование
nano .env

# Вставить API ключи
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 3. Запуск

```bash
# Запуск сервера
bash run.sh

# Или в фоновом режиме (nohup)
nohup bash run.sh > logs/server.log 2>&1 &

# Проверка
ps aux | grep python
```

### 4. Доступ с телефона

Откройте браузер на телефоне:
```
http://localhost:8000
http://localhost:8000/docs  # API документация
```

---

## 🎯 Best Practices

### 1. Логирование

- Сохраняйте логи на внешнее хранилище (SD карта)
- Настройте ротацию логов
- Периодически очищайте старые логи

### 2. Питание

- Подключите телефон к зарядке
- Отключите энергосбережение для Termux
- Настройте wake lock

### 3. Сеть

- Используйте WiFi для стабильности
- Настройте статический IP
- Откройте порты в firewall

### 4. Безопасность

- Не коммитьте `.env` файл
- Используйте testnet для тестов
- Ограничьте доступ к API

---

*Last updated: 22 февраля 2026*
