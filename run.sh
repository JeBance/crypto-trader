#!/bin/bash
# ===========================================
# Crypto Trader - Self-Healing Server Runner
# ===========================================
# Этот скрипт запускает сервер с автоматической
# проверкой и установкой зависимостей.
#
# Использование:
#   bash run.sh [--debug] [--no-auto-update]
#   bash run.sh --setup    # Только установка
# ===========================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$PROJECT_ROOT/logs/server.log"
PID_FILE="$PROJECT_ROOT/logs/server.pid"
RESTART_COUNT=0
MAX_RESTARTS=10
RESTART_WINDOW=300  # 5 minutes

# Array to store restart times
declare -a RESTART_TIMES=()

# Setup flag
RUN_SETUP=false

# Ensure directories exist
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/data"

# Function to print colored output
print_header() {
    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Function to check if Python is available
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python не найден! Установите Python 3.10+"
        exit 1
    fi
    
    print_info "Python: $($PYTHON_CMD --version)"
}

# Function to check if virtual environment exists
check_venv() {
    if [ -d "$PROJECT_ROOT/venv" ]; then
        print_info "Виртуальное окружение найдено"
        source "$PROJECT_ROOT/venv/bin/activate"
    else
        print_warning "Виртуальное окружение не найдено"
    fi
}

# Function to check dependencies
check_dependencies() {
    print_info "Проверка зависимостей..."
    
    # Check if venv is active
    if [ -z "$VIRTUAL_ENV" ]; then
        print_warning "Виртуальное окружение не активно"
        return 1
    fi
    
    # Check critical packages
    $PYTHON_CMD -c "import fastapi" 2>/dev/null || {
        print_warning "FastAPI не установлен, установка..."
        pip install -r "$PROJECT_ROOT/backend/requirements.txt"
    }
    
    print_success "Зависимости установлены"
}

# Function to clean old restart times
clean_restart_times() {
    local now=$(date +%s)
    local cutoff=$((now - RESTART_WINDOW))
    
    # Filter out old restart times
    RESTART_TIMES=($(for t in "${RESTART_TIMES[@]}"; do
        if [ "$t" -gt "$cutoff" ]; then
            echo "$t"
        fi
    done))
}

# Function to check if we can restart
can_restart() {
    clean_restart_times
    
    if [ ${#RESTART_TIMES[@]} -ge $MAX_RESTARTS ]; then
        return 1
    fi
    
    return 0
}

# Function to run the server
run_server() {
    local args="$@"
    
    print_info "Starting Crypto Trader Server..."
    print_info "Arguments: $args"
    print_info "Log file: $LOG_FILE"
    print_info ""
    print_info "Press Ctrl+C to stop"
    print_info "=" | awk '{for(i=1;i<=60;i++)printf "="; print ""}'
    
    while true; do
        # Check restart limit
        if ! can_restart; then
            print_error "Maximum restarts ($MAX_RESTARTS) exceeded in ${RESTART_WINDOW}s"
            print_error "Manual intervention required!"
            exit 1
        fi
        
        # Increment restart count
        RESTART_COUNT=$((RESTART_COUNT + 1))
        RESTART_TIMES+=($(date +%s))
        
        if [ $RESTART_COUNT -gt 1 ]; then
            print_warning "Restart attempt #$RESTART_COUNT"
        fi
        
        # Run the server
        print_info "Starting server process..."
        
        # Run Python script with output to both log and terminal
        $PYTHON_CMD "$PROJECT_ROOT/run_server.py" $args 2>&1 | tee -a "$LOG_FILE"
        
        EXIT_CODE=$?
        
        # Handle exit codes
        case $EXIT_CODE in
            0)
                print_success "Server stopped gracefully"
                exit 0
                ;;
            130)
                print_info "Server interrupted (Ctrl+C)"
                exit 0
                ;;
            *)
                print_error "Server crashed with exit code $EXIT_CODE"
                print_warning "Restarting in 5 seconds..."
                sleep 5
                ;;
        esac
    done
}

# Function to show status
show_status() {
    print_info "Server Status:"
    print_info "  Restart Count: $RESTART_COUNT"
    print_info "  Recent Restarts: ${#RESTART_TIMES[@]}"
    print_info "  Log File: $LOG_FILE"
    
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p $pid > /dev/null 2>&1; then
            print_success "Server running (PID: $pid)"
        else
            print_warning "Server not running (stale PID file)"
        fi
    else
        print_info "No PID file found"
    fi
}

# Function to show help
show_help() {
    echo "Crypto Trader Server Runner"
    echo ""
    echo "Использование: $0 [OPTIONS]"
    echo ""
    echo "Опции:"
    echo "  --debug           Включить debug режим"
    echo "  --no-auto-update  Отключить авто-обновление"
    echo "  --setup           Запустить установку зависимостей"
    echo "  --status          Показать статус сервера"
    echo "  --help            Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0                          # Обычный запуск"
    echo "  $0 --debug                  # Debug режим"
    echo "  $0 --setup                  # Только установка"
    echo "  $0 --no-auto-update         # Без авто-обновления"
    echo ""
}

# Main
main() {
    echo ""
    echo "=" | awk '{for(i=1;i<=60;i++)printf "="; print ""}'
    echo "🚀 Crypto Trader - Self-Healing Server"
    echo "=" | awk '{for(i=1;i<=60;i++)printf "="; print ""}'
    echo ""

    # Parse arguments
    SERVER_ARGS=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --debug)
                SERVER_ARGS="$SERVER_ARGS --debug"
                shift
                ;;
            --no-auto-update)
                SERVER_ARGS="$SERVER_ARGS --no-auto-update"
                shift
                ;;
            --setup)
                RUN_SETUP=true
                shift
                ;;
            --status)
                check_python
                check_venv
                show_status
                exit 0
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "Неизвестная опция: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Run setup if requested or if first run
    if [ "$RUN_SETUP" = true ] || [ ! -d "$PROJECT_ROOT/venv" ]; then
        print_header "📦 Проверка зависимостей"
        
        if [ -f "$PROJECT_ROOT/setup.sh" ]; then
            print_info "Запуск установки зависимостей..."
            bash "$PROJECT_ROOT/setup.sh" --skip-packages
            print_success "Установка завершена"
        else
            print_warning "setup.sh не найден, пропускаем установку"
        fi
    fi
    
    # Run pre-checks
    check_python
    check_venv
    check_dependencies
    
    echo ""
    
    # Run the server
    run_server "$SERVER_ARGS"
}

# Run main function
main "$@"
