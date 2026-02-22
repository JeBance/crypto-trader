#!/bin/bash
# ===========================================
# Crypto Trader - Скрипт установки для Termux
# ===========================================

set -e

echo "🚀 Crypto Trader - Установка"
echo "============================="

# Проверка Termux
if [ -z "$PREFIX" ]; then
    echo "⚠️  Предупреждение: Этот скрипт предназначен для Termux"
    echo "   Продолжение установки..."
fi

# Обновление пакетов
echo "📦 Обновление пакетов..."
pkg update -y || true

# Установка зависимостей
echo "📦 Установка зависимостей..."
pkg install -y python git curl wget

# Проверка Python
python_version=$(python --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "🐍 Версия Python: $python_version"

# Создание виртуального окружения
echo "📦 Создание виртуального окружения..."
python -m venv venv

# Активация виртуального окружения
echo "🔌 Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей Python
echo "📦 Установка зависимостей Python..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# Создание директорий
echo "📁 Создание директорий..."
mkdir -p data logs

# Копирование конфигурации
echo "⚙️  Настройка конфигурации..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Создан файл .env - отредактируйте его с вашими API ключами"
fi

if [ ! -f config.yaml ]; then
    cp config.yaml.example config.yaml
    echo "✅ Создан файл config.yaml - настройте стратегии"
fi

# Установка frontend зависимостей (опционально)
echo "📦 Установка frontend зависимостей (опционально)..."
read -p "Установить frontend зависимости? (y/n): " install_frontend
if [ "$install_frontend" = "y" ]; then
    if command -v npm &> /dev/null; then
        cd frontend
        npm install
        cd ..
        echo "✅ Frontend зависимости установлены"
    else
        echo "⚠️  npm не найден - пропущена установка frontend"
    fi
fi

echo ""
echo "============================="
echo "✅ Установка завершена!"
echo ""
echo "📝 Следующие шаги:"
echo "   1. Отредактируйте .env с вашими API ключами"
echo "   2. Настройте config.yaml"
echo "   3. Запустите: bash scripts/start.sh"
echo ""
