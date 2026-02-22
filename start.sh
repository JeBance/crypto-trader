#!/bin/bash
# Crypto Trader - Auto-restart server wrapper

PROJECT_ROOT="/data/data/com.termux/files/home/crypto-trader"
BACKEND_DIR="$PROJECT_ROOT/backend"
LOG_FILE="$PROJECT_ROOT/logs/server.log"

echo "=========================================="
echo "🚀 Crypto Trader Server"
echo "=========================================="
echo "Project Root: $PROJECT_ROOT"
echo "Log File: $LOG_FILE"
echo ""

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting server..."
    
    # Запуск сервера
    cd "$BACKEND_DIR"
    PYTHONPATH="$BACKEND_DIR" python3 app/main.py >> "$LOG_FILE" 2>&1
    EXIT_CODE=$?
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Server exited with code $EXIT_CODE"
    
    # Проверка кода выхода
    if [ $EXIT_CODE -eq 3 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔄 Restart requested (exit code 3)"
        sleep 2
        continue
    elif [ $EXIT_CODE -eq 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Server stopped normally"
        break
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ Server crashed (exit code $EXIT_CODE)"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restarting in 5 seconds..."
        sleep 5
    fi
done

echo "=========================================="
echo "👋 Server stopped"
echo "=========================================="
