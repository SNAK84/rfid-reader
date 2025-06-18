#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Функция для вывода сообщений
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    print_error "Этот скрипт должен быть запущен с правами root"
    exit 1
fi

# Определение пути установки
INSTALL_DIR=$(pwd)

print_message "Быстрая установка RFID Reader System в $INSTALL_DIR"

# Создание временной директории для клонирования
TEMP_DIR=$(mktemp -d)
print_message "Создание временной директории: $TEMP_DIR"

# Клонирование репозитория во временную директорию
print_message "Клонирование репозитория..."
git clone https://github.com/snak84/rfid-reader.git "$TEMP_DIR" || {
    print_error "Ошибка при клонировании репозитория"
    rm -rf "$TEMP_DIR"
    exit 1
}

# Копирование файлов проекта
print_message "Копирование файлов проекта..."
cp -r "$TEMP_DIR"/* "$INSTALL_DIR/"
cp -r "$TEMP_DIR"/.* "$INSTALL_DIR/" 2>/dev/null || true

# Очистка временной директории
rm -rf "$TEMP_DIR"

print_message "Файлы проекта скопированы"
print_message "Теперь запустите: ./install.sh" 