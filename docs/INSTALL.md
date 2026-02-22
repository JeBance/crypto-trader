# 📦 Crypto Trader — Полная инструкция по установке

Подробное руководство по установке Crypto Trader на различные платформы.

---

## 🎯 Выбор способа установки

### Быстрая таблица

| Платформа | Способ | Время | Сложность |
|-----------|--------|-------|-----------|
| **Android (Termux)** | Автоматический | 3-5 мин | ⭐ Легко |
| **Linux (Ubuntu/Debian)** | Автоматический | 2-3 мин | ⭐ Легко |
| **macOS** | Автоматический | 3-5 мин | ⭐⭐ Средне |
| **Windows (WSL)** | Ручной | 5-10 мин | ⭐⭐⭐ Сложно |

---

## 📱 Способ 1: Android (Termux) — Рекомендуемый

### Шаг 1: Установка Termux

1. **Скачайте Termux** из F-Droid (рекомендуется):
   - https://f-droid.org/en/packages/com.termux/

2. **Или из Google Play** (устаревшая версия):
   - https://play.google.com/store/apps/details?id=com.termux

> ⚠️ **Важно:** Версия из F-Droid новее и поддерживается лучше!

### Шаг 2: Первоначальная настройка Termux

Откройте Termux и выполните:

```bash
# Разрешение на доступ к хранилищу (опционально)
termux-setup-storage

# Обновление пакетов
pkg update && pkg upgrade

# Установка Git
pkg install git
```

### Шаг 3: Клонирование репозитория

```bash
# Клонирование
git clone https://github.com/JeBance/crypto-trader.git

# Переход в директорию
cd crypto-trader
```

### Шаг 4: Автоматическая установка

```bash
# Запуск авто-установщика
bash setup.sh
```

**Что установится:**
- Python 3.10+
- Node.js 18+
- npm
- Все Python зависимости
- Все Frontend зависимости

### Шаг 5: Настройка конфигурации

```bash
# Редактирование .env
nano .env
```

**Минимальная конфигурация:**
```bash
# Режим торговли (paper = демо)
TRADING_MODE=paper

# Binance (testnet = тестовая сеть)
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
BINANCE_TESTNET=true

# Telegram (опционально)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

**Сохранение в nano:**
1. `Ctrl+O` → `Enter` (сохранить)
2. `Ctrl+X` (выйти)

### Шаг 6: Запуск сервера

```bash
# Обычный запуск
bash run.sh

# Или в debug режиме (подробнее логи)
bash run.sh --debug
```

### Шаг 7: Доступ к приложению

Откройте браузер на телефоне:

```
http://localhost:8000      # Backend API
http://localhost:8000/docs # Swagger UI
http://localhost:3000      # Frontend (если установлен)
```

---

## 🐧 Способ 2: Linux (Ubuntu/Debian)

### Шаг 1: Установка системных зависимостей

```bash
# Обновление
sudo apt update

# Установка пакетов
sudo apt install -y python3 python3-pip python3-venv \
                    git curl wget nodejs npm \
                    build-essential libjpeg-dev zlib1g-dev
```

### Шаг 2: Клонирование репозитория

```bash
git clone https://github.com/JeBance/crypto-trader.git
cd crypto-trader
```

### Шаг 3: Автоматическая установка

```bash
bash setup.sh
```

### Шаг 4: Настройка и запуск

```bash
# Настройка
nano .env

# Запуск
bash run.sh
```

---

## 🍎 Способ 3: macOS

### Шаг 1: Установка Homebrew (если нет)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Шаг 2: Установка зависимостей

```bash
brew install python git node
```

### Шаг 3: Клонирование и установка

```bash
git clone https://github.com/JeBance/crypto-trader.git
cd crypto-trader
bash setup.sh
```

### Шаг 4: Настройка и запуск

```bash
nano .env
bash run.sh --debug
```

---

## 🪟 Способ 4: Windows (WSL2)

### Шаг 1: Установка WSL2

```powershell
# В PowerShell (Admin)
wsl --install
```

Перезагрузите компьютер.

### Шаг 2: Установка Ubuntu

```powershell
# В PowerShell
wsl --install -d Ubuntu
```

### Шаг 3: Настройка WSL

Откройте Ubuntu из меню Пуск:
1. Создайте пользователя
2. Задайте пароль

### Шаг 4: Установка зависимостей

```bash
# Обновление
sudo apt update && sudo apt upgrade -y

# Установка пакетов
sudo apt install -y python3 python3-pip python3-venv \
                    git curl wget nodejs npm

# Установка Node.js (если старая версия)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### Шаг 5: Клонирование и установка

```bash
git clone https://github.com/JeBance/crypto-trader.git
cd crypto-trader
bash setup.sh
```

### Шаг 6: Запуск

```bash
bash run.sh --debug
```

### Шаг 7: Доступ из Windows

Откройте браузер в Windows:
```
http://localhost:8000
http://localhost:8000/docs
```

---

## 🔧 Решение проблем

### Проблема: "Python not found"

**Termux:**
```bash
pkg install python
```

**Linux:**
```bash
sudo apt install python3 python3-pip python3-venv
```

**macOS:**
```bash
brew install python
```

---

### Проблема: "Permission denied"

```bash
# Дать права скриптам
chmod +x setup.sh run.sh

# Запустить снова
bash setup.sh
```

---

### Проблема: "Port 8000 already in use"

**Вариант 1: Найти и убить процесс**
```bash
lsof -i :8000
kill <PID>
```

**Вариант 2: Изменить порт**
```bash
# В .env
PORT=8001
```

---

### Проблема: "ModuleNotFoundError: No module named 'fastapi'"

```bash
# Активировать venv
source venv/bin/activate

# Установить зависимости
pip install -r backend/requirements.txt
```

---

### Проблема: "npm install fails"

**Очистка кэша:**
```bash
npm cache clean --force
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

### Проблема: "Git clone fails"

**Проверка соединения:**
```bash
ping github.com
```

**Использование HTTPS вместо SSH:**
```bash
git clone https://github.com/JeBance/crypto-trader.git
```

---

### Проблема: "Virtual environment not created"

**Ручное создание:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

---

### Проблема: "Setup.sh fails"

**Пошаговая установка:**
```bash
# 1. Системные пакеты
pkg install python git nodejs  # Termux
# или
sudo apt install python3 git nodejs  # Linux

# 2. venv
python3 -m venv venv
source venv/bin/activate

# 3. Python зависимости
pip install -r backend/requirements.txt

# 4. Запуск
bash run.sh
```

---

## 📊 Проверка установки

### 1. Проверка версий

```bash
# Python
python --version  # Должен быть 3.10+

# Git
git --version

# Node.js
node --version  # Должен быть 18+

# pip
pip --version
```

### 2. Проверка зависимостей

```bash
source venv/bin/activate

# Проверка FastAPI
python -c "import fastapi; print('FastAPI OK')"

# Проверка SQLAlchemy
python -c "import sqlalchemy; print('SQLAlchemy OK')"

# Проверка uvicorn
python -c "import uvicorn; print('Uvicorn OK')"
```

### 3. Тестовый запуск

```bash
# Запуск
bash run.sh --debug

# В другом терминале — проверка API
curl http://localhost:8000/api/health
```

**Ожидаемый ответ:**
```json
{
  "status": "healthy",
  "name": "Crypto Trader",
  "version": "0.2.0",
  "timestamp": "2026-02-22T..."
}
```

---

## 🎓 Дополнительные команды

### Управление сервером

```bash
# Запуск в фоне
nohup bash run.sh > logs/server.log 2>&1 &

# Проверка статуса
bash run.sh --status

# Остановка (Ctrl+C в терминале)

# Перезапуск
pkill -f run_server.py
bash run.sh
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

### Обновление

```bash
# Автоматически (встроено в сервер)
# Сервер сам проверит обновления через 5 минут

# Вручную
git pull origin gh-pages
bash run.sh --setup  # Переустановит зависимости
```

---

## 📞 Если ничего не помогло

### 1. Включите debug логирование

```bash
bash run.sh --debug 2>&1 | tee logs/full_debug.log
```

### 2. Соберите информацию

```bash
# Версия Python
python --version

# ОС
uname -a  # Linux/macOS
# или
cat /etc/os-release  # Linux

# Версия setup.sh
head -5 setup.sh
```

### 3. Создайте Issue

Перейдите на: https://github.com/JeBance/crypto-trader/issues

**Приложите:**
- Версию ОС
- Версию Python
- Полный лог ошибки
- Шаги воспроизведения

---

## ✅ Чек-лист успешной установки

- [ ] Python 3.10+ установлен
- [ ] Git установлен
- [ ] Node.js 18+ установлен (опционально)
- [ ] Репозиторий склонирован
- [ ] `venv/` директория создана
- [ ] Python зависимости установлены
- [ ] `.env` файл создан и настроен
- [ ] Сервер запускается (`bash run.sh`)
- [ ] API отвечает (`curl http://localhost:8000/api/health`)
- [ ] Логи пишутся в `logs/server.log`

---

*Последнее обновление: 22 февраля 2026*
