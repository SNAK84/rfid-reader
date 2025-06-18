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

# Определение пути установки и пользователя
INSTALL_DIR=$(pwd)
SERVICE_USER=${SUDO_USER:-$USER}

print_message "Обновление RFID Reader System в $INSTALL_DIR"

# Создание резервной копии
BACKUP_DIR="/tmp/rfid-reader-backup-$(date +%Y%m%d-%H%M%S)"
print_message "Создание резервной копии в $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Резервное копирование важных файлов
if [ -f "$INSTALL_DIR/.env" ]; then
    cp "$INSTALL_DIR/.env" "$BACKUP_DIR/"
    print_message "Сохранен .env файл"
fi

if [ -d "$INSTALL_DIR/logs" ]; then
    cp -r "$INSTALL_DIR/logs" "$BACKUP_DIR/"
    print_message "Сохранены логи"
fi

# Остановка сервиса
print_message "Остановка сервиса..."
systemctl stop rfid-reader.service 2>/dev/null || true

# Создание временной директории для нового кода
TEMP_DIR=$(mktemp -d)
print_message "Загрузка обновлений..."

# Клонирование репозитория во временную директорию
git clone https://github.com/snak84/rfid-reader.git "$TEMP_DIR" || {
    print_error "Ошибка при клонировании репозитория"
    rm -rf "$TEMP_DIR"
    exit 1
}

# Удаление старых файлов (кроме важных)
print_message "Обновление файлов проекта..."
find "$INSTALL_DIR" -maxdepth 1 -type f ! -name '.env' ! -name 'install.sh' ! -name 'update.sh' -delete
find "$INSTALL_DIR" -maxdepth 1 -type d ! -name 'logs' ! -name '__pycache__' ! -name '.git' -exec rm -rf {} + 2>/dev/null || true

# Копирование новых файлов
cp -r "$TEMP_DIR"/* "$INSTALL_DIR/"
cp -r "$TEMP_DIR"/.* "$INSTALL_DIR/" 2>/dev/null || true

# Восстановление важных файлов
if [ -f "$BACKUP_DIR/.env" ]; then
    cp "$BACKUP_DIR/.env" "$INSTALL_DIR/"
    print_message "Восстановлен .env файл"
fi

# Очистка временных файлов
rm -rf "$TEMP_DIR"

# Установка прав
print_message "Установка прав доступа..."
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/wg_daemon.py"
chmod +x "$INSTALL_DIR/monitor.py"
chmod +x "$INSTALL_DIR/test_system.py"

# Обновление systemd сервиса
print_message "Обновление systemd сервиса..."
if [ -f "$INSTALL_DIR/rfid-reader.service" ]; then
    sed "s|/opt/rfid-reader|$INSTALL_DIR|g" "$INSTALL_DIR/rfid-reader.service" > /etc/systemd/system/rfid-reader.service
    sed -i "s/User=pi/User=$SERVICE_USER/g" /etc/systemd/system/rfid-reader.service
    sed -i "s/Group=pi/Group=$SERVICE_USER/g" /etc/systemd/system/rfid-reader.service
    systemctl daemon-reload
fi

# Обновление ротации логов
print_message "Обновление ротации логов..."
if [ -f "$INSTALL_DIR/logrotate.conf" ]; then
    sed "s|/opt/rfid-reader|$INSTALL_DIR|g" "$INSTALL_DIR/logrotate.conf" > /etc/logrotate.d/rfid-reader
    sed -i "s/User=pi/User=$SERVICE_USER/g" /etc/logrotate.d/rfid-reader
    sed -i "s/Group=pi/Group=$SERVICE_USER/g" /etc/logrotate.d/rfid-reader
fi

# Обновление виртуального окружения
print_message "Обновление Python зависимостей..."
if [ -d "$INSTALL_DIR/venv" ]; then
    source "$INSTALL_DIR/venv/bin/activate"
    pip install -r "$INSTALL_DIR/requirements.txt" --upgrade
    deactivate
else
    print_warning "Виртуальное окружение не найдено, создание нового..."
    python3 -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"
    pip install -r "$INSTALL_DIR/requirements.txt"
    deactivate
fi

# Тестирование системы
print_message "Запуск тестирования системы..."
if [ -f "$INSTALL_DIR/test_system.py" ]; then
    cd "$INSTALL_DIR"
    source venv/bin/activate
    python3 test_system.py
    deactivate
else
    print_warning "Скрипт тестирования не найден"
fi

# Запуск сервиса
print_message "Запуск сервиса..."
systemctl start rfid-reader.service

print_message "Обновление завершено!"
print_message "Резервная копия сохранена в: $BACKUP_DIR"
print_message "Для проверки статуса: systemctl status rfid-reader.service"
print_message "Для мониторинга: python3 monitor.py" 