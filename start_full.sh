#!/bin/bash
# ===========================================
# Crypto Trader - Full Stack Runner
# Запускает Backend (8000) + Frontend (3000)
# ===========================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}============================================================${NC}"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python не найден!"
        exit 1
    fi
    print_info "Python: $($PYTHON_CMD --version)"
}

# Check if Node.js is available
check_node() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_info "Node.js: $NODE_VERSION"
    else
        print_error "Node.js не найден!"
        exit 1
    fi
}

# Start Backend
start_backend() {
    print_header "🚀 Запуск Backend (port $BACKEND_PORT)"
    
    cd "$PROJECT_ROOT"
    export PYTHONPATH="$PROJECT_ROOT/backend:$PYTHONPATH"
    
    # Start backend in background
    nohup $PYTHON_CMD -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port $BACKEND_PORT \
        --log-level info \
        > logs/backend.log 2>&1 &
    
    BACKEND_PID=$!
    echo $BACKEND_PID > logs/backend.pid
    
    print_info "Backend PID: $BACKEND_PID"
    print_info "Log file: logs/backend.log"
    
    # Wait for backend to start
    sleep 5
    
    # Check if backend is running
    if curl -s http://localhost:$BACKEND_PORT/api/health > /dev/null 2>&1; then
        print_success "Backend запущен на http://localhost:$BACKEND_PORT"
        print_info "API Docs: http://localhost:$BACKEND_PORT/docs"
    else
        print_error "Backend не запустился! Проверьте logs/backend.log"
        cat logs/backend.log
        exit 1
    fi
}

# Start Frontend
start_frontend() {
    print_header "🎨 Запуск Frontend (port $FRONTEND_PORT)"
    
    cd "$PROJECT_ROOT/frontend"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_warning "node_modules не найден, установка зависимостей..."
        npm install
    fi
    
    # Start frontend in background
    nohup npm run dev \
        -- --host 0.0.0.0 --port $FRONTEND_PORT \
        > logs/frontend.log 2>&1 &
    
    FRONTEND_PID=$!
    echo $FRONTEND_PID > logs/frontend.pid
    
    print_info "Frontend PID: $FRONTEND_PID"
    print_info "Log file: logs/frontend.log"
    
    # Wait for frontend to start
    sleep 8
    
    # Check if frontend is running
    if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
        print_success "Frontend запущен на http://localhost:$FRONTEND_PORT"
    else
        print_error "Frontend не запустился! Проверьте logs/frontend.log"
        cat logs/frontend.log
        exit 1
    fi
}

# Show status
show_status() {
    print_header "📊 Статус серверов"
    
    echo ""
    echo "Backend (port $BACKEND_PORT):"
    if [ -f "logs/backend.pid" ]; then
        PID=$(cat logs/backend.pid)
        if ps -p $PID > /dev/null 2>&1; then
            print_success "Работает (PID: $PID)"
            print_info "API: http://localhost:$BACKEND_PORT"
            print_info "Docs: http://localhost:$BACKEND_PORT/docs"
        else
            print_error "Не работает (stale PID file)"
        fi
    else
        print_warning "PID файл не найден"
    fi
    
    echo ""
    echo "Frontend (port $FRONTEND_PORT):"
    if [ -f "logs/frontend.pid" ]; then
        PID=$(cat logs/frontend.pid)
        if ps -p $PID > /dev/null 2>&1; then
            print_success "Работает (PID: $PID)"
            print_info "UI: http://localhost:$FRONTEND_PORT"
        else
            print_error "Не работает (stale PID file)"
        fi
    else
        print_warning "PID файл не найден"
    fi
}

# Stop all servers
stop_all() {
    print_header "🛑 Остановка серверов"
    
    if [ -f "logs/backend.pid" ]; then
        PID=$(cat logs/backend.pid)
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID 2>/dev/null || true
            print_info "Backend остановлен (PID: $PID)"
        fi
        rm logs/backend.pid
    fi
    
    if [ -f "logs/frontend.pid" ]; then
        PID=$(cat logs/frontend.pid)
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID 2>/dev/null || true
            print_info "Frontend остановлен (PID: $PID)"
        fi
        rm logs/frontend.pid
    fi
    
    # Also kill by process name
    pkill -f "uvicorn app.main" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    
    print_success "Все серверы остановлены"
}

# Show help
show_help() {
    echo "Crypto Trader - Full Stack Runner"
    echo ""
    echo "Использование: $0 [COMMAND]"
    echo ""
    echo "Команды:"
    echo "  start       Запустить Backend + Frontend"
    echo "  stop        Остановить все серверы"
    echo "  status      Показать статус серверов"
    echo "  backend     Запустить только Backend"
    echo "  frontend    Запустить только Frontend"
    echo "  help        Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 start      # Запустить всё"
    echo "  $0 stop       # Остановить всё"
    echo "  $0 backend    # Только backend"
    echo ""
    echo "После запуска:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend:  http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
}

# Main
main() {
    mkdir -p "$PROJECT_ROOT/logs"
    
    case "${1:-start}" in
        start)
            print_header "🚀 Crypto Trader - Full Stack Start"
            check_python
            check_node
            start_backend
            start_frontend
            echo ""
            print_success "=============================================="
            echo ""
            print_info "📱 Frontend UI: http://localhost:3000"
            print_info "🔧 Backend API: http://localhost:8000"
            print_info "📖 API Docs:    http://localhost:8000/docs"
            echo ""
            print_info "Для остановки: $0 stop"
            print_info "Логи: logs/backend.log, logs/frontend.log"
            echo ""
            ;;
        stop)
            stop_all
            ;;
        status)
            show_status
            ;;
        backend)
            check_python
            start_backend
            ;;
        frontend)
            check_node
            start_frontend
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Неизвестная команда: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
