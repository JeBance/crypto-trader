#!/bin/bash
# ===========================================
# Crypto Trader - Auto-Installer Script
# 
# Автоматическая проверка и установка
# всех зависимостей для Termux/Android
#
# Использование:
#   bash setup.sh [--force] [--no-frontend]
# ===========================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$PROJECT_ROOT/logs/setup.log"
VENV_DIR="$PROJECT_ROOT/venv"
MIN_PYTHON_VERSION="3.10"
MIN_NODE_VERSION="18"

# Flags
FORCE_INSTALL=false
INSTALL_FRONTEND=true
SKIP_PACKAGES=false

# Counters
INSTALLED_COUNT=0
FAILED_COUNT=0

# ============================================
# Helper Functions
# ============================================

print_header() {
    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
    log_message "OK" "$1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    log_message "WARN" "$1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    log_message "ERROR" "$1"
}

print_step() {
    echo -e "${WHITE}→${NC} $1"
}

log_message() {
    local level="$1"
    local message="$2"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message" >> "$LOG_FILE" 2>/dev/null || true
}

# ============================================
# Detection Functions
# ============================================

detect_environment() {
    print_header "🔍 Определение окружения"
    
    # Check if running in Termux
    if [ -n "$PREFIX" ] && [ -d "/data/data/com.termux" ]; then
        IS_TERMUX=true
        print_info "Обнаружен Termux на Android"
    else
        IS_TERMUX=false
        print_info "Обнаружена стандартная Linux/Unix среда"
    fi
    
    # Check OS
    if [ "$IS_TERMUX" = true ]; then
        OS_NAME="Android/Termux"
    elif command -v apt &> /dev/null; then
        OS_NAME="Debian/Ubuntu"
        PACKAGE_MANAGER="apt"
    elif command -v yum &> /dev/null; then
        OS_NAME="RHEL/CentOS"
        PACKAGE_MANAGER="yum"
    elif command -v brew &> /dev/null; then
        OS_NAME="macOS"
        PACKAGE_MANAGER="brew"
    else
        OS_NAME="Unknown"
        PACKAGE_MANAGER="unknown"
    fi
    
    print_info "ОС: $OS_NAME"
    print_info "Package Manager: $PACKAGE_MANAGER"
    
    # Create logs directory
    mkdir -p "$PROJECT_ROOT/logs"
    touch "$LOG_FILE"
}

check_python() {
    print_step "Проверка Python..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        PYTHON_CMD=""
    fi
    
    if [ -n "$PYTHON_CMD" ]; then
        PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
        print_info "Python: $PYTHON_VERSION"
        
        # Check minimum version
        if [ "$(printf '%s\n' "$MIN_PYTHON_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$MIN_PYTHON_VERSION" ]; then
            print_success "Python версия подходит"
            return 0
        else
            print_warning "Python версия устарела (требуется $MIN_PYTHON_VERSION+)"
            return 1
        fi
    else
        print_warning "Python не найден"
        return 1
    fi
}

check_git() {
    print_step "Проверка Git..."
    
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version | cut -d' ' -f3)
        print_info "Git: $GIT_VERSION"
        print_success "Git установлен"
        return 0
    else
        print_warning "Git не найден"
        return 1
    fi
}

check_node() {
    print_step "Проверка Node.js..."
    
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version | cut -d'v' -f2)
        print_info "Node.js: $NODE_VERSION"
        
        # Check minimum version
        if [ "$(printf '%s\n' "$MIN_NODE_VERSION" "$NODE_VERSION" | sort -V | head -n1)" = "$MIN_NODE_VERSION" ]; then
            print_success "Node.js версия подходит"
            return 0
        else
            print_warning "Node.js версия устарела (требуется $MIN_NODE_VERSION+)"
            return 1
        fi
    else
        print_warning "Node.js не найден"
        return 1
    fi
}

check_npm() {
    print_step "Проверка npm..."
    
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        print_info "npm: $NPM_VERSION"
        print_success "npm установлен"
        return 0
    else
        print_warning "npm не найден"
        return 1
    fi
}

check_venv() {
    print_step "Проверка виртуального окружения..."
    
    if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
        print_info "Виртуальное окружение найдено"
        print_success "Виртуальное окружение готово"
        return 0
    else
        print_warning "Виртуальное окружение не найдено"
        return 1
    fi
}

check_dependencies() {
    print_step "Проверка Python зависимостей..."
    
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
        
        # Check critical packages
        local missing=()
        
        if ! python -c "import fastapi" 2>/dev/null; then
            missing+=("fastapi")
        fi
        
        if ! python -c "import uvicorn" 2>/dev/null; then
            missing+=("uvicorn")
        fi
        
        if ! python -c "import sqlalchemy" 2>/dev/null; then
            missing+=("sqlalchemy")
        fi
        
        if [ ${#missing[@]} -eq 0 ]; then
            print_success "Все зависимости установлены"
            return 0
        else
            print_warning "Отсутствуют пакеты: ${missing[*]}"
            return 1
        fi
    else
        print_warning "Виртуальное окружение не активно"
        return 1
    fi
}

# ============================================
# Installation Functions
# ============================================

install_packages_termux() {
    print_header "📦 Установка пакетов в Termux"
    
    print_step "Обновление пакетов..."
    pkg update -y || {
        print_warning "Не удалось обновить пакеты"
    }
    
    # Packages to install
    local packages=(
        "python"
        "git"
        "curl"
        "wget"
        "nodejs"
        "npm"
        "build-essential"
        "libjpeg-turbo"
        "zlib"
        "libxml2"
        "libxslt"
    )
    
    print_step "Установка зависимостей..."
    for pkg_name in "${packages[@]}"; do
        if pkg list-installed | grep -q "^$pkg_name "; then
            print_info "$pkg_name уже установлен"
        else
            print_step "Установка $pkg_name..."
            if pkg install -y "$pkg_name" 2>&1 | tee -a "$LOG_FILE"; then
                print_success "$pkg_name установлен"
                ((INSTALLED_COUNT++))
            else
                print_error "Не удалось установить $pkg_name"
                ((FAILED_COUNT++))
            fi
        fi
    done
}

install_packages_linux() {
    print_header "📦 Установка пакетов в Linux"
    
    case $PACKAGE_MANAGER in
        apt)
            print_step "Обновление пакетов..."
            sudo apt update || print_warning "Не удалось обновить пакеты"
            
            print_step "Установка зависимостей..."
            sudo apt install -y python3 python3-pip python3-venv git curl wget nodejs npm build-essential libjpeg-dev zlib1g-dev libxml2-dev libxslt1-dev
            ;;
        yum)
            print_step "Установка зависимостей..."
            sudo yum install -y python3 python3-pip git curl wget nodejs npm
            ;;
        *)
            print_warning "Неизвестный package manager: $PACKAGE_MANAGER"
            print_info "Установите зависимости вручную"
            return 1
            ;;
    esac
}

install_packages_macos() {
    print_header "📦 Установка пакетов в macOS"
    
    if ! command -v brew &> /dev/null; then
        print_warning "Homebrew не найден"
        print_info "Установите Homebrew: https://brew.sh"
        return 1
    fi
    
    print_step "Установка зависимостей..."
    brew install python git node
}

create_venv() {
    print_header "🐍 Создание виртуального окружения"
    
    if [ -d "$VENV_DIR" ]; then
        print_info "Удаление старого виртуального окружения"
        rm -rf "$VENV_DIR"
    fi
    
    print_step "Создание виртуального окружения..."
    if $PYTHON_CMD -m venv "$VENV_DIR" 2>&1 | tee -a "$LOG_FILE"; then
        print_success "Виртуальное окружение создано"
    else
        print_error "Не удалось создать виртуальное окружение"
        return 1
    fi
    
    # Activate
    print_step "Активация виртуального окружения..."
    source "$VENV_DIR/bin/activate"
    print_success "Виртуальное окружение активировано"
    
    # Upgrade pip
    print_step "Обновление pip..."
    pip install --upgrade pip 2>&1 | tee -a "$LOG_FILE"
    print_success "pip обновлён"
}

install_python_dependencies() {
    print_header "📦 Установка Python зависимостей"
    
    # Activate venv
    source "$VENV_DIR/bin/activate"
    
    print_step "Установка зависимостей из requirements.txt..."
    if [ -f "$PROJECT_ROOT/backend/requirements.txt" ]; then
        if pip install -r "$PROJECT_ROOT/backend/requirements.txt" 2>&1 | tee -a "$LOG_FILE"; then
            print_success "Python зависимости установлены"
        else
            print_error "Не удалось установить Python зависимости"
            return 1
        fi
    else
        print_error "requirements.txt не найден"
        return 1
    fi
}

install_frontend_dependencies() {
    print_header "📦 Установка Frontend зависимостей"
    
    if [ "$INSTALL_FRONTEND" = false ]; then
        print_info "Пропускаем установку frontend (флаг --no-frontend)"
        return 0
    fi
    
    if [ ! -d "$PROJECT_ROOT/frontend" ]; then
        print_warning "Frontend директория не найдена"
        return 0
    fi
    
    cd "$PROJECT_ROOT/frontend"
    
    print_step "Установка npm зависимостей..."
    if npm install 2>&1 | tee -a "$LOG_FILE"; then
        print_success "Frontend зависимости установлены"
    else
        print_error "Не удалось установить frontend зависимости"
        print_warning "Frontend будет недоступен"
    fi
    
    cd "$PROJECT_ROOT"
}

setup_configuration() {
    print_header "⚙️  Настройка конфигурации"
    
    # .env file
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        print_step "Создание .env файла..."
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        print_success ".env файл создан"
        print_warning "Отредактируйте .env и добавьте ваши API ключи"
    else
        print_info ".env файл уже существует"
    fi
    
    # config.yaml file
    if [ ! -f "$PROJECT_ROOT/config.yaml" ]; then
        print_step "Создание config.yaml файла..."
        cp "$PROJECT_ROOT/config.yaml.example" "$PROJECT_ROOT/config.yaml"
        print_success "config.yaml файл создан"
    else
        print_info "config.yaml файл уже существует"
    fi
    
    # Create directories
    print_step "Создание необходимых директорий..."
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/data"
    print_success "Директории созданы"
}

# ============================================
# Main Installation Flow
# ============================================

run_installation() {
    print_header "🚀 Crypto Trader - Auto-Installer"
    
    echo -e "${WHITE}Этот скрипт автоматически установит все зависимости${NC}"
    echo -e "${WHITE}для запуска Crypto Trader на вашем устройстве${NC}"
    echo ""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                FORCE_INSTALL=true
                print_info "Режим force включён"
                shift
                ;;
            --no-frontend)
                INSTALL_FRONTEND=false
                print_info "Frontend не будет установлен"
                shift
                ;;
            --skip-packages)
                SKIP_PACKAGES=true
                print_info "Пропускаем установку системных пакетов"
                shift
                ;;
            --help)
                echo "Использование: bash setup.sh [OPTIONS]"
                echo ""
                echo "Опции:"
                echo "  --force          Пересоздать всё заново"
                echo "  --no-frontend    Не устанавливать frontend"
                echo "  --skip-packages  Пропустить установку системных пакетов"
                echo "  --help           Показать эту справку"
                exit 0
                ;;
            *)
                print_error "Неизвестная опция: $1"
                exit 1
                ;;
        esac
    done
    
    # Detect environment
    detect_environment
    
    # Check what needs to be installed
    print_header "📋 Проверка зависимостей"
    
    NEEDS_PYTHON=false
    NEEDS_GIT=false
    NEEDS_NODE=false
    NEEDS_VENV=false
    NEEDS_DEPS=false
    
    check_python || NEEDS_PYTHON=true
    check_git || NEEDS_GIT=true
    
    if [ "$INSTALL_FRONTEND" = true ]; then
        check_node || NEEDS_NODE=true
        check_npm || NEEDS_NODE=true
    fi
    
    check_venv || NEEDS_VENV=true
    check_dependencies || NEEDS_DEPS=true
    
    # Install missing components
    if [ "$NEEDS_PYTHON" = true ] || [ "$NEEDS_GIT" = true ] || [ "$NEEDS_NODE" = true ]; then
        print_header "📦 Установка системных пакетов"
        
        if [ "$SKIP_PACKAGES" = true ]; then
            print_warning "Пропускаем установку системных пакетов"
        elif [ "$IS_TERMUX" = true ]; then
            install_packages_termux
        elif [ "$OS_NAME" = "macOS" ]; then
            install_packages_macos
        else
            install_packages_linux
        fi
        
        # Re-check
        check_python || { print_error "Не удалось установить Python"; exit 1; }
        check_git || { print_error "Не удалось установить Git"; exit 1; }
    fi
    
    # Create virtual environment
    if [ "$NEEDS_VENV" = true ] || [ "$FORCE_INSTALL" = true ]; then
        create_venv
    else
        # Just activate existing
        source "$VENV_DIR/bin/activate"
    fi
    
    # Install Python dependencies
    if [ "$NEEDS_DEPS" = true ] || [ "$FORCE_INSTALL" = true ]; then
        install_python_dependencies
    fi
    
    # Install frontend dependencies
    if [ "$INSTALL_FRONTEND" = true ]; then
        if [ "$NEEDS_NODE" = true ]; then
            print_warning "Node.js не установлен, frontend не будет доступен"
        else
            install_frontend_dependencies
        fi
    fi
    
    # Setup configuration
    setup_configuration
    
    # Summary
    print_header "✅ Установка завершена"
    
    echo -e "${GREEN}Успешно установлено: ${INSTALLED_COUNT}${NC}"
    if [ $FAILED_COUNT -gt 0 ]; then
        echo -e "${RED}Не удалось установить: ${FAILED_COUNT}${NC}"
    fi
    echo ""
    
    print_success "Crypto Trader готов к запуску!"
    echo ""
    echo -e "${WHITE}Следующие шаги:${NC}"
    echo ""
    echo "  1. Отредактируйте ${CYAN}.env${NC} и добавьте API ключи:"
    echo "     ${YELLOW}nano .env${NC}"
    echo ""
    echo "  2. Запустите сервер:"
    echo "     ${YELLOW}bash run.sh${NC}"
    echo ""
    echo "  3. Откройте в браузере:"
    echo "     ${CYAN}http://localhost:8000/docs${NC}"
    echo ""
    
    if [ "$IS_TERMUX" = true ]; then
        echo -e "${WHITE}Совет для Termux:${NC}"
        echo "  Для работы в фоне используйте:"
        echo "     ${YELLOW}nohup bash run.sh > logs/server.log 2>&1 &${NC}"
        echo ""
    fi
    
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}📖 Документация: docs/SELF_HEALING_SERVER.md${NC}"
    echo -e "${CYAN}🚀 Быстрый старт: README.md${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""
}

# ============================================
# Run Installation
# ============================================

run_installation "$@"
