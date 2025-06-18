# RFID Card Reader System

Система для считывания RFID-карт с использованием Raspberry Pi.

## Требования

- Python 3.7+
- Raspberry Pi
- MySQL/MariaDB
- RFID-считыватель (подключенный к GPIO пинам 23 и 24)
- Git

## Установка

1. Скачайте скрипт установки:
```bash
wget https://raw.githubusercontent.com/your-username/rfid-reader/main/install.sh
```

2. Запустите скрипт установки:
```bash
sudo chmod +x install.sh
sudo ./install.sh
```

Во время установки вам будет предложено:
- Выбрать путь для установки (по умолчанию /opt/rfid-reader)
- Указать пользователя для запуска сервиса (по умолчанию текущий пользователь)

Скрипт установки выполнит следующие действия:
- Клонирует репозиторий
- Создаст необходимые директории
- Установит зависимости Python
- Создаст пользователя базы данных
- Настроит systemd сервис
- Создаст конфигурационный файл

## Конфигурация

После установки отредактируйте файл конфигурации:
```bash
sudo nano /opt/rfid-reader/.env  # или путь, который вы указали при установке
```

Установите правильные значения для:
- Параметров базы данных
- GPIO пинов
- Путей к логам

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

## Структура проекта

- `wg_daemon.py` - основной демон
- `database.py` - класс для работы с базой данных
- `rfid_reader.py` - класс для работы с RFID-считывателем
- `rfid-reader.service` - systemd сервис
- `requirements.txt` - зависимости проекта
- `.env` - конфигурационный файл
- `install.sh` - скрипт установки

## Логирование

Логи сохраняются в:
- `$INSTALL_DIR/logs/wg_daemon.log` - логи приложения
- `journalctl -u rfid-reader.service` - системные логи

## Безопасность

- Все конфиденциальные данные хранятся в файле .env
- Реализована защита от SQL-инъекций
- Настроено логирование всех операций
- Сервис запускается от указанного непривилегированного пользователя
- Файлы установлены с правильными правами доступа 