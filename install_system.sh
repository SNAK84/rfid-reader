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

# Проверка и установка Python3
if ! command -v python3 &> /dev/null; then
    print_message "Установка Python3..."
    apt-get update && apt-get install -y python3 || {
        print_error "Ошибка при установке Python3"
        exit 1
    }
fi

# Установка pip3, если он не установлен
if ! command -v pip3 &> /dev/null; then
    print_message "Установка pip3..."
    apt-get update && apt-get install -y python3-pip || {
        print_error "Ошибка при установке pip3"
        exit 1
    }
fi

# Установка MySQL, если он не установлен
if ! command -v mysql &> /dev/null; then
    print_message "Установка MySQL..."
    apt-get update && apt-get install -y mysql-server || {
        print_error "Ошибка при установке MySQL"
        exit 1
    }
fi

# Установка Git, если он не установлен
if ! command -v git &> /dev/null; then
    print_message "Установка Git..."
    apt-get update && apt-get install -y git || {
        print_error "Ошибка при установке Git"
        exit 1
    }
fi

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    print_error "Этот скрипт должен быть запущен с правами root"
    exit 1
fi

# Определение пути установки и пользователя
INSTALL_DIR=$(pwd)
SERVICE_USER=${SUDO_USER:-$USER}

# Проверка существования пользователя
if ! id "$SERVICE_USER" &>/dev/null; then
    print_error "Пользователь $SERVICE_USER не существует"
    exit 1
fi

# Создание директорий
print_message "Создание необходимых директорий..."
mkdir -p "$INSTALL_DIR/logs"
mkdir -p /var/run

# Клонирование репозитория
print_message "Клонирование репозитория..."
if [ -d "$INSTALL_DIR/.git" ]; then
    print_warning "Директория уже содержит git репозиторий, пропускаем клонирование"
elif [ "$(ls -A $INSTALL_DIR)" ]; then
    # Директория не пуста
    if [ "$(ls -A $INSTALL_DIR | wc -l)" -eq 1 ] && [ -f "$INSTALL_DIR/install.sh" ]; then
        print_message "В директории только install.sh, удаляем его и клонируем репозиторий..."
        rm "$INSTALL_DIR/install.sh"
        git clone https://github.com/snak84/rfid-reader.git "$INSTALL_DIR" || {
            print_error "Ошибка при клонировании репозитория"
            exit 1
        }
    else
        print_warning "Директория не пуста, создаем временную директорию для клонирования..."
        TEMP_DIR=$(mktemp -d)
        git clone https://github.com/snak84/rfid-reader.git "$TEMP_DIR" || {
            print_error "Ошибка при клонировании репозитория"
            rm -rf "$TEMP_DIR"
            exit 1
        }
        
        # Копируем файлы из временной директории
        print_message "Копирование файлов проекта..."
        cp -r "$TEMP_DIR"/* "$INSTALL_DIR/"
        cp -r "$TEMP_DIR"/.* "$INSTALL_DIR/" 2>/dev/null || true
        rm -rf "$TEMP_DIR"
        print_message "Файлы проекта скопированы"
    fi
else
    git clone https://github.com/snak84/rfid-reader.git "$INSTALL_DIR" || {
        print_error "Ошибка при клонировании репозитория"
        exit 1
    }
fi

# Копирование файла сервиса
print_message "Настройка systemd сервиса..."
sed "s|/opt/rfid-reader|$INSTALL_DIR|g" "$INSTALL_DIR/rfid-reader.service" > /etc/systemd/system/rfid-reader.service
sed -i "s/User=pi/User=$SERVICE_USER/g" /etc/systemd/system/rfid-reader.service
sed -i "s/Group=pi/Group=$SERVICE_USER/g" /etc/systemd/system/rfid-reader.service

# Установка прав
print_message "Установка прав доступа..."
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"
touch /var/run/rfid-reader.pid
chown "$SERVICE_USER:$SERVICE_USER" /var/run/rfid-reader.pid

# Установка системных Python пакетов
print_message "Установка системных Python пакетов..."
apt-get update && apt-get install -y python3-rpi.gpio python3-mysql.connector python3-dotenv || {
    print_warning "Не удалось установить системные пакеты, попробуем установить через pip"
    pip3 install --break-system-packages RPi.GPIO mysql-connector-python python-dotenv daemonize || {
        print_error "Не удалось установить Python зависимости"
        exit 1
    }
}

# Настройка ротации логов
print_message "Настройка ротации логов..."
if [ -f "$INSTALL_DIR/logrotate.conf" ]; then
    sed "s|/opt/rfid-reader|$INSTALL_DIR|g" "$INSTALL_DIR/logrotate.conf" > /etc/logrotate.d/rfid-reader
    sed -i "s/User=pi/User=$SERVICE_USER/g" /etc/logrotate.d/rfid-reader
    sed -i "s/Group=pi/Group=$SERVICE_USER/g" /etc/logrotate.d/rfid-reader
    print_message "Ротация логов настроена"
else
    print_warning "Файл logrotate.conf не найден, ротация логов не настроена"
fi

# Создание исполняемых скриптов
print_message "Создание исполняемых скриптов..."
chmod +x "$INSTALL_DIR/wg_daemon.py"
chmod +x "$INSTALL_DIR/monitor.py"
chmod +x "$INSTALL_DIR/test_system.py"

# Запрос настроек MySQL
read -p "Введите хост MySQL (по умолчанию localhost): " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "Введите имя пользователя MySQL (по умолчанию rfid_reader): " DB_USER
DB_USER=${DB_USER:-rfid_reader}

read -p "Введите пароль для пользователя MySQL: " DB_PASSWORD
while [ -z "$DB_PASSWORD" ]; do
    print_error "Пароль не может быть пустым"
    read -p "Введите пароль для пользователя MySQL: " DB_PASSWORD
done

read -p "Введите имя базы данных (по умолчанию rfid_cards): " DB_NAME
DB_NAME=${DB_NAME:-rfid_cards}

# Создание .env файла, если его нет
if [ ! -f "$INSTALL_DIR/.env" ]; then
    print_message "Создание конфигурационного файла..."
    cat > "$INSTALL_DIR/.env" << EOL
# Database configuration
DB_HOST=$DB_HOST
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME

# GPIO configuration
DATA0_PIN=24
DATA1_PIN=23

# Logging configuration
LOG_DIR=$INSTALL_DIR/logs
PID_FILE=/var/run/rfid-reader.pid
EOL
    print_warning "Пожалуйста, отредактируйте файл $INSTALL_DIR/.env и установите правильные значения"
fi

# Создание базы данных
print_message "Создание базы данных..."
if [ "$DB_HOST" = "localhost" ]; then
    mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME;"
    mysql -e "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
    mysql -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
    mysql -e "FLUSH PRIVILEGES;"
    mysql $DB_NAME -e "CREATE TABLE IF NOT EXISTS pass (id INT AUTO_INCREMENT PRIMARY KEY, time INT NOT NULL, card VARCHAR(255) NOT NULL);"
else
    print_warning "Создание базы данных на удаленном хосте $DB_HOST пропущено. Пожалуйста, создайте базу данных и пользователя вручную."
fi

# Настройка systemd
print_message "Настройка systemd сервиса..."
systemctl daemon-reload
systemctl enable rfid-reader.service

# Тестирование системы
print_message "Запуск тестирования системы..."
if [ -f "$INSTALL_DIR/test_system.py" ]; then
    cd "$INSTALL_DIR"
    python3 test_system.py
else
    print_warning "Скрипт тестирования не найден"
fi

print_message "Установка завершена!"
print_warning "Не забудьте отредактировать файл $INSTALL_DIR/.env и установить правильные значения"
print_message "Для запуска сервиса выполните: systemctl start rfid-reader.service"
print_message "Для мониторинга используйте: python3 monitor.py"
print_message "Для тестирования используйте: python3 test_system.py" 