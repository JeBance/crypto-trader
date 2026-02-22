#!/bin/bash
# ===========================================
# Crypto Trader - Скрипт запуска
# ===========================================

set -e

echo "🚀 Crypto Trader - Запуск"
echo "========================="

# Проверка виртуального окружения
if [ -z "$VIRTUAL_ENV" ]; then
    echo "🔌 Активация виртуального окружения..."
    source venv/bin/activate
fi

# Создание директорий
mkdir -p data logs

# Проверка конфигурации
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "   Скопируйте .env.example в .env и настройте"
    exit 1
fi

# Загрузка переменных окружения
set -a
source .env
set +a

# Запуск сервера
echo "🌐 Запуск сервера на http://$HOST:$PORT"
echo ""

# Опции запуска
case "${1:-}" in
    --dev)
        echo "🔧 Режим разработки (auto-reload)"
        uvicorn app.main:app --reload --host $HOST --port $PORT
        ;;
    --frontend)
        echo "🎨 Запуск frontend + backend"
        # Запуск в фоне
        uvicorn app.main:app --host $HOST --port $PORT &
        BACKEND_PID=$!
        
        # Запуск frontend
        cd frontend
        npm run dev
        cd ..
        
        # Ожидание остановки
        wait $BACKEND_PID
        ;;
    *)
        echo "⚡ Продуктовый режим"
        uvicorn app.main:app --host $HOST --port $PORT --workers 1
        ;;
esac
