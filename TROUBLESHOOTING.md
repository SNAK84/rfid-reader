# Руководство по устранению неполадок

## Общие проблемы и решения

### 1. Сервис не запускается

**Симптомы:**
- `systemctl status rfid-reader.service` показывает ошибки
- Сервис не отвечает на команды запуска

**Диагностика:**
```bash
# Проверка статуса сервиса
sudo systemctl status rfid-reader.service

# Просмотр логов сервиса
sudo journalctl -u rfid-reader.service -n 50

# Проверка конфигурации
sudo systemctl cat rfid-reader.service
```

**Возможные решения:**

#### Проблема с правами доступа
```bash
# Проверка прав на файлы
ls -la /opt/rfid-reader/

# Исправление прав
sudo chown -R pi:pi /opt/rfid-reader/
sudo chmod -R 755 /opt/rfid-reader/
```

#### Проблема с Python окружением
```bash
# Активация виртуального окружения
source /opt/rfid-reader/venv/bin/activate

# Проверка зависимостей
pip list

# Переустановка зависимостей
pip install -r requirements.txt
```

#### Проблема с конфигурацией
```bash
# Проверка .env файла
cat /opt/rfid-reader/.env

# Проверка переменных окружения
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('DB_HOST:', os.getenv('DB_HOST'))"
```

### 2. Ошибки подключения к базе данных

**Симптомы:**
- Ошибки "Connection refused" или "Access denied"
- Демон не может сохранить данные карт

**Диагностика:**
```bash
# Проверка статуса MySQL
sudo systemctl status mysql

# Проверка подключения к MySQL
mysql -u rfid_reader -p

# Тест подключения через Python
python3 -c "
from database import Database
try:
    db = Database()
    print('Подключение успешно')
except Exception as e:
    print('Ошибка:', e)
"
```

**Возможные решения:**

#### MySQL не запущен
```bash
sudo systemctl start mysql
sudo systemctl enable mysql
```

#### Неправильные учетные данные
```bash
# Создание пользователя заново
sudo mysql -e "
CREATE USER IF NOT EXISTS 'rfid_reader'@'localhost' IDENTIFIED BY 'новый_пароль';
GRANT ALL PRIVILEGES ON rfid_cards.* TO 'rfid_reader'@'localhost';
FLUSH PRIVILEGES;
"
```

#### Проблема с правами доступа к БД
```bash
# Проверка существования базы данных
sudo mysql -e "SHOW DATABASES;"

# Создание базы данных
sudo mysql -e "CREATE DATABASE IF NOT EXISTS rfid_cards;"
```

### 3. Проблемы с GPIO

**Симптомы:**
- Ошибки "GPIO setup failed"
- RFID-карты не считываются

**Диагностика:**
```bash
# Проверка доступности GPIO
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN)
GPIO.setup(24, GPIO.IN)
print('GPIO доступен')
GPIO.cleanup()
"
```

**Возможные решения:**

#### Неправильные номера пинов
```bash
# Проверка конфигурации пинов
grep "DATA.*PIN" .env

# Изменение пинов в .env
nano .env
```

#### Проблемы с правами доступа
```bash
# Добавление пользователя в группу gpio
sudo usermod -a -G gpio pi

# Проверка групп
groups pi
```

#### Аппаратные проблемы
```bash
# Проверка подключения RFID-считывателя
# Убедитесь, что:
# - Считыватель подключен к правильным пинам
# - Питание подается корректно
# - Кабели не повреждены
```

### 4. Проблемы с логированием

**Симптомы:**
- Логи не создаются
- Файлы логов слишком большие
- Ошибки записи в лог

**Диагностика:**
```bash
# Проверка директории логов
ls -la logs/

# Проверка размера логов
du -sh logs/

# Проверка прав на запись
touch logs/test.log
```

**Возможные решения:**

#### Проблемы с правами доступа
```bash
# Исправление прав на директорию логов
sudo chown -R pi:pi logs/
sudo chmod -R 755 logs/
```

#### Ротация логов не настроена
```bash
# Настройка ротации логов
sudo cp logrotate.conf /etc/logrotate.d/rfid-reader

# Принудительная ротация
sudo logrotate -f /etc/logrotate.d/rfid-reader
```

#### Диск заполнен
```bash
# Проверка свободного места
df -h

# Очистка старых логов
find logs/ -name "*.log.*" -mtime +7 -delete
```

### 5. Проблемы с производительностью

**Симптомы:**
- Высокая загрузка CPU
- Медленное считывание карт
- Задержки в сохранении данных

**Диагностика:**
```bash
# Мониторинг ресурсов
htop

# Проверка логов на ошибки
tail -f logs/wg_daemon.log | grep ERROR

# Статистика работы демона
python3 monitor.py
```

**Возможные решения:**

#### Оптимизация настроек
```bash
# Увеличение задержки между циклами чтения
# В wg_daemon.py измените time.sleep(0.1) на time.sleep(0.2)
```

#### Проблемы с базой данных
```bash
# Проверка индексов
mysql -u rfid_reader -p rfid_cards -e "SHOW INDEX FROM pass;"

# Создание индекса по времени
mysql -u rfid_reader -p rfid_cards -e "CREATE INDEX idx_time ON pass(time);"
```

## Инструменты диагностики

### Скрипт тестирования системы
```bash
# Полное тестирование всех компонентов
python3 test_system.py
```

### Скрипт мониторинга
```bash
# Однократная проверка
python3 monitor.py

# Непрерывный мониторинг
python3 monitor.py --continuous
```

### Прямое управление демоном
```bash
# Запуск в режиме отладки
python3 wg_daemon.py start

# Проверка статуса
python3 wg_daemon.py status

# Остановка
python3 wg_daemon.py stop
```

## Часто задаваемые вопросы

### Q: Как перезапустить сервис после изменений?
```bash
sudo systemctl restart rfid-reader.service
```

### Q: Как проверить, что карты считываются?
```bash
# Просмотр логов в реальном времени
tail -f logs/wg_daemon.log

# Проверка базы данных
mysql -u rfid_reader -p rfid_cards -e "SELECT * FROM pass ORDER BY time DESC LIMIT 10;"
```

### Q: Как изменить конфигурацию?
```bash
# Редактирование .env файла
nano .env

# Перезапуск сервиса
sudo systemctl restart rfid-reader.service
```

### Q: Как обновить систему?
```bash
# Остановка сервиса
sudo systemctl stop rfid-reader.service

# Обновление кода
git pull

# Перезапуск сервиса
sudo systemctl start rfid-reader.service
```

## Контакты для поддержки

При возникновении проблем, которые не описаны в данном руководстве:

1. Проверьте логи: `tail -f logs/wg_daemon.log`
2. Запустите тестирование: `python3 test_system.py`
3. Соберите информацию о системе: `python3 monitor.py`
4. Обратитесь к разработчику с описанием проблемы и результатами диагностики 