# RFID Card Reader System

Система для считывания RFID-карт с использованием Raspberry Pi.

## Требования

- Python 3.7+
- Raspberry Pi
- MySQL/MariaDB
- RFID-считыватель (подключенный к GPIO пинам 23 и 24)
- Git

## Установка

### Вариант 1: Стандартная установка (рекомендуется)

1. Скачайте скрипт установки:
```bash
wget https://raw.githubusercontent.com/snak84/rfid-reader/main/install.sh
```

2. Запустите скрипт установки:
```bash
sudo chmod +x install.sh
sudo ./install.sh
```

### Вариант 2: Системная установка (для систем с ограничениями)

Если у вас возникают проблемы с виртуальными окружениями, используйте системную установку:

```bash
wget https://raw.githubusercontent.com/snak84/rfid-reader/main/install_system.sh
sudo chmod +x install_system.sh
sudo ./install_system.sh
```

### Вариант 3: Быстрая установка в непустую директорию

Если директория не пуста:

```bash
wget https://raw.githubusercontent.com/snak84/rfid-reader/main/quick_install.sh
sudo chmod +x quick_install.sh
sudo ./quick_install.sh
sudo ./install.sh
```

### Вариант 4: Обновление существующей установки

```bash
wget https://raw.githubusercontent.com/snak84/rfid-reader/main/update.sh
sudo chmod +x update.sh
sudo ./update.sh
```

## Решение проблем установки

### Проблема: "externally-managed-environment"

Если вы видите ошибку:
```
error: externally-managed-environment
```

Используйте системную установку:
```bash
sudo ./install_system.sh
```

### Проблема: "Директория не пуста"

Если директория уже содержит файлы:
```bash
sudo ./quick_install.sh
sudo ./install.sh
```

### Проблема: "deactivate: команда не найдена"

Это нормально, если виртуальное окружение не было активировано. Установка продолжится автоматически.

## Конфигурация

После установки отредактируйте файл конфигурации:
```bash
sudo nano .env  # файл находится в текущей директории
```

Установите правильные значения для:
- Параметров базы данных
- GPIO пинов
- Путей к логам

Пример содержимого .env:
```
# Database configuration
DB_HOST=localhost
DB_USER=rfid_reader
DB_PASSWORD=your_password
DB_NAME=rfid_cards

# GPIO configuration
DATA0_PIN=24
DATA1_PIN=23

# Logging configuration
LOG_DIR=./logs
PID_FILE=/var/run/rfid-reader.pid
```

## Использование

### Управление сервисом через systemd

Запуск сервиса:
```bash
sudo systemctl start rfid-reader.service
```

Остановка сервиса:
```bash
sudo systemctl stop rfid-reader.service
```

Перезапуск сервиса:
```bash
sudo systemctl restart rfid-reader.service
```

Проверка статуса:
```bash
sudo systemctl status rfid-reader.service
```

Просмотр логов:
```bash
sudo journalctl -u rfid-reader.service -f
```

### Прямое управление демоном

Запуск демона:
```bash
python3 wg_daemon.py start
```

Остановка демона:
```bash
python3 wg_daemon.py stop
```

Проверка статуса:
```bash
python3 wg_daemon.py status
```

Перезапуск:
```bash
python3 wg_daemon.py restart
```

## Мониторинг

### Скрипт мониторинга

Для проверки состояния системы используйте скрипт мониторинга:

```bash
python3 monitor.py
```

Непрерывный мониторинг:
```bash
python3 monitor.py --continuous
```

Скрипт проверяет:
- Статус systemd сервиса
- Подключение к базе данных
- Активность за последние 10 минут
- Размер файлов логов
- Последние записи в логах

### Ротация логов

Для автоматической ротации логов установите конфигурацию:

```bash
sudo cp logrotate.conf /etc/logrotate.d/rfid-reader
```

## Структура проекта

- `wg_daemon.py` - основной демон с улучшенным мониторингом
- `database.py` - класс для работы с базой данных с валидацией
- `rfid_reader.py` - класс для работы с RFID-считывателем с таймаутами
- `rfid-reader.service` - systemd сервис
- `requirements.txt` - зависимости проекта
- `.env` - конфигурационный файл
- `install.sh` - основной скрипт установки
- `install_system.sh` - системная установка (без виртуального окружения)
- `quick_install.sh` - быстрая установка в непустую директорию
- `update.sh` - скрипт обновления
- `monitor.py` - скрипт мониторинга системы
- `test_system.py` - скрипт тестирования системы
- `logrotate.conf` - конфигурация ротации логов
- `TROUBLESHOOTING.md` - руководство по устранению неполадок

## Логирование

Логи сохраняются в:
- `$INSTALL_DIR/logs/wg_daemon.log` - логи приложения (с ротацией)
- `journalctl -u rfid-reader.service` - системные логи

### Статистика работы

Демон автоматически ведет статистику:
- Время работы
- Количество обработанных карт
- Количество ошибок
- Статистика выводится каждые 100 карт или 10 минут

## Безопасность

- Все конфиденциальные данные хранятся в файле .env
- Реализована защита от SQL-инъекций
- Валидация всех входных данных
- Настроено логирование всех операций
- Сервис запускается от указанного непривилегированного пользователя
- Файлы установлены с правильными правами доступа

## Улучшения в последней версии

### Исправленные проблемы:
- ✅ Исправлен отсутствующий импорт `time` в database.py
- ✅ Добавлена валидация данных карт
- ✅ Улучшена обработка ошибок GPIO
- ✅ Добавлены таймауты для чтения карт
- ✅ Реализована ротация логов
- ✅ Исправлены проблемы с виртуальными окружениями
- ✅ Добавлена поддержка системных пакетов

### Новые возможности:
- 🔧 Скрипт мониторинга системы
- 📊 Статистика работы демона
- 🔄 Автоматическая ротация логов
- 🛡️ Улучшенная обработка ошибок
- ⚡ Retry-логика для базы данных
- 📈 Детальное логирование операций
- 🔄 Множественные варианты установки
- 🧪 Автоматическое тестирование системы

## База данных

Структура таблицы:
```sql
CREATE TABLE pass (
    id INT AUTO_INCREMENT PRIMARY KEY,
    time INT NOT NULL,
    card VARCHAR(255) NOT NULL
);
```

## Устранение неполадок

### Проверка состояния системы:
```bash
python3 test_system.py
```

### Просмотр последних ошибок:
```bash
tail -f logs/wg_daemon.log | grep ERROR
```

### Проверка подключения к БД:
```bash
python3 -c "from database import Database; db = Database(); print('OK' if db.test_connection() else 'ERROR')"
```

### Перезапуск сервиса:
```bash
sudo systemctl restart rfid-reader.service
```

Подробное руководство по устранению неполадок см. в файле `TROUBLESHOOTING.md`. 