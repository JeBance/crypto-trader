#!/bin/bash
# ===========================================
# Crypto Trader - Self-Healing Server Runner
# ===========================================
# This script runs the server with automatic
# restart on crash and log display.
#
# Usage:
#   bash run.sh [--debug] [--no-auto-update]
# ===========================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Ensure directories exist
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/data"

# Function to print colored output
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
        print_error "Python not found! Please install Python 3.10+"
        exit 1
    fi
    
    print_info "Using Python: $($PYTHON_CMD --version)"
}

# Function to check if virtual environment exists
check_venv() {
    if [ -d "$PROJECT_ROOT/venv" ]; then
        print_info "Virtual environment found"
        source "$PROJECT_ROOT/venv/bin/activate"
    else
        print_warning "Virtual environment not found, using system Python"
    fi
}

# Function to check dependencies
check_dependencies() {
    print_info "Checking dependencies..."
    
    # Check critical packages
    $PYTHON_CMD -c "import fastapi" 2>/dev/null || {
        print_warning "FastAPI not installed, installing dependencies..."
        pip install -r "$PROJECT_ROOT/backend/requirements.txt"
    }
    
    print_success "Dependencies OK"
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
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --debug           Enable debug mode"
    echo "  --no-auto-update  Disable automatic updates"
    echo "  --status          Show server status"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                          # Normal start"
    echo "  $0 --debug                  # Debug mode"
    echo "  $0 --no-auto-update         # Disable auto-update"
    echo "  $0 --debug --no-auto-update # Both options"
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
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
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
