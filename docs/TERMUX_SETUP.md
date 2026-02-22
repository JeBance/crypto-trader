# 📱 Crypto Trader на Android (Termux) — Руководство по установке

Пошаговая инструкция по установке и запуску Crypto Trader на Android смартфоне.

---

## 📋 Требования

- Устройство на базе **Android**
- Свободно **~500 MB** места
- **Termux** (установить из F-Droid)
- Доступ к интернету (для установки и обновлений)

---

## 🚀 Установка (5 минут)

### Шаг 1: Установка Termux

1. **Скачайте Termux из F-Droid** (рекомендуется):
   - Откройте https://f-droid.org/en/packages/com.termux/
   - Нажмите "Download APK"
   - Установите APK файл

> ⚠️ **Не устанавливайте Termux из Google Play!** Версия там устарела.

### Шаг 2: Первоначальная настройка

Откройте Termux и выполните команды:

```bash
# Разрешение на доступ к хранилищу
termux-setup-storage

# Обновление пакетов
pkg update && pkg upgrade

# Установка Git
pkg install git
```

### Шаг 3: Клонирование проекта

```bash
# Клонирование репозитория
git clone https://github.com/JeBance/crypto-trader.git

# Переход в директорию проекта
cd crypto-trader
```

### Шаг 4: Запуск установки

```bash
# Запуск авто-установщика
bash setup.sh
```

**Что установится:**
- Python 3.10+
- Node.js 18+
- Все зависимости
- Виртуальное окружение

**Время установки:** 3-5 минут (зависит от интернета)

### Шаг 5: Первый запуск

```bash
# Запуск сервера
bash run.sh
```

**Сервер запустится и:**
- ✅ Создаст `.env` файл с дефолтными значениями
- ✅ Инициализирует базу данных
- ✅ Загрузит стратегии (RSI, Crossover, MACD)
- ✅ Начнёт логирование

---

## 🌐 Доступ к приложению

Откройте браузер на телефоне:

```
http://localhost:8000      # Backend API
http://localhost:8000/docs # API документация
http://localhost:3000      # Frontend UI
```

---

## ⚙️ Настройка

### 1. Добавление API ключей (опционально)

Для реальной торговли добавьте API ключи:

```bash
# Редактирование .env
nano .env
```

**Добавьте ключи Binance или Bybit:**
```bash
# Binance
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
BINANCE_TESTNET=true

# Bybit
BYBIT_API_KEY=your_key_here
BYBIT_API_SECRET=your_secret_here
BYBIT_TESTNET=true
```

**Сохранение в nano:**
- `Ctrl+O` → `Enter` (сохранить)
- `Ctrl+X` (выйти)

### 2. Включение стратегий

1. Откройте `http://localhost:3000/strategies`
2. Включите нужные стратегии (toggle switch)
3. Настройте параметры (опционально)

---

## 📱 Работа в фоне

### Запуск в фоновом режиме

```bash
# Запуск с nohup (работает после закрытия Termux)
nohup bash run.sh > logs/server.log 2>&1 &

# Проверка работы
ps aux | grep python
```

### Остановка сервера

```bash
# Найти процесс
ps aux | grep run_server

# Остановить
kill <PID>
```

---

## 🔧 Управление

### Проверка статуса

```bash
# Статус сервера
bash run.sh --status

# Просмотр логов
tail -f logs/server.log

# Последние 50 строк логов
tail -50 logs/server.log
```

### Обновление

```bash
# Сервер обновляется автоматически каждые 5 минут

# Или вручную
git pull origin gh-pages
bash run.sh --setup
```

### Перезапуск

```bash
# Остановить текущий процесс
pkill -f run_server.py

# Запустить снова
bash run.sh
```

---

## 🎯 Быстрый старт (команды для копирования)

```bash
# 1. Установка Termux пакетов
pkg update && pkg upgrade
pkg install git python nodejs

# 2. Клонирование
git clone https://github.com/JeBance/crypto-trader.git
cd crypto-trader

# 3. Установка
bash setup.sh

# 4. Запуск
bash run.sh
```

---

## 🛠️ Решение проблем

### Проблема: "Permission denied"

```bash
# Дать права скриптам
chmod +x setup.sh run.sh

# Запустить снова
bash setup.sh
```

### Проблема: "Python not found"

```bash
# Установить Python
pkg install python
```

### Проблема: "Port 8000 already in use"

```bash
# Найти процесс
lsof -i :8000

# Остановить
kill <PID>

# Или изменить порт в .env
PORT=8001
```

### Проблема: "No module named 'fastapi'"

```bash
# Активировать venv
source venv/bin/activate

# Установить зависимости
pip install -r backend/requirements.txt
```

### Проблема: Сервер не запускается

```bash
# Посмотреть логи
tail -100 logs/server.log

# Запустить в debug режиме
bash run.sh --debug
```

---

## 📊 Потребление ресурсов

| Ресурс | Ожидается |
|--------|-----------|
| **RAM** | 200-400 MB |
| **CPU** | 5-15% (в простое) |
| **Storage** | ~500 MB |
| **Network** | Минимальный |
| **Battery** | ~5-10% в час |

---

## 💡 Советы для Android

### 1. Оптимизация батареи

- Подключите телефон к зарядке
- Отключите энергосбережение для Termux
- Настройте wake lock:
  ```bash
  termux-wake-lock
  ```

### 2. Доступ из локальной сети

Для доступа с компьютера в той же WiFi сети:

```bash
# Узнать IP телефона
ifconfig

# В .env установить
HOST=0.0.0.0

# Доступ с компьютера
http://<PHONE_IP>:8000
```

### 3. Автостарт при загрузке

Создайте скрипт `~/.termux/boot/startup.sh`:

```bash
mkdir -p ~/.termux/boot
nano ~/.termux/boot/startup.sh
```

**Содержимое:**
```bash
#!/data/data/com.termux/files/usr/bin/bash
cd ~/crypto-trader
source venv/bin/activate
bash run.sh
```

**Дать права:**
```bash
chmod +x ~/.termux/boot/startup.sh
```

---

## 📚 Документация

- [USER_GUIDE.md](USER_GUIDE.md) — Работа через UI
- [STRATEGIES.md](STRATEGIES.md) — Описание стратегий
- [API.md](API.md) — API документация
- [SELF_HEALING_SERVER.md](SELF_HEALING_SERVER.md) — Автономная работа

---

## ✅ Чек-лист установки

- [ ] Termux установлен (из F-Droid)
- [ ] Пакеты обновлены
- [ ] Git установлен
- [ ] Проект склонирован
- [ ] setup.sh выполнен успешно
- [ ] Сервер запущен
- [ ] UI открывается в браузере
- [ ] API отвечает (curl http://localhost:8000/api/health)

---

## 🎉 Готово!

Crypto Trader v1.0.0 установлен и работает на вашем Android устройстве!

**Следующие шаги:**
1. Откройте `http://localhost:3000` в браузере
2. Включите стратегии на `/strategies`
3. Добавьте API ключи (опционально)
4. Мониторьте Dashboard

---

*Last updated: 22 февраля 2026*
