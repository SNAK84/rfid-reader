#!/usr/bin/env python3
import os
import sys
import time
import logging
import signal
from daemonize import Daemonize
from dotenv import load_dotenv
from database import Database
from rfid_reader import RFIDReader

load_dotenv()

# Настройка логирования
log_dir = os.getenv('LOG_DIR')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'wg_daemon.log')

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

class WGDaemon:
    def __init__(self):
        self.pid_file = os.getenv('PID_FILE')
        self.db = None
        self.reader = None
        self.running = False
        self.cards_processed = 0
        self.errors_count = 0
        self.start_time = None

    def signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        logging.info(f"Получен сигнал {signum}, завершение работы...")
        self.running = False

    def setup(self):
        try:
            # Настройка обработчиков сигналов
            signal.signal(signal.SIGTERM, self.signal_handler)
            signal.signal(signal.SIGINT, self.signal_handler)
            
            # Инициализация компонентов
            self.db = Database()
            self.reader = RFIDReader()
            
            # Тестирование подключений
            if not self.db.test_connection():
                raise Exception("Не удалось подключиться к базе данных")
            
            logging.info("Демон успешно инициализирован")
            return True
        except Exception as e:
            logging.error(f"Ошибка инициализации демона: {e}")
            return False

    def log_statistics(self):
        """Логирование статистики работы"""
        if self.start_time:
            uptime = time.time() - self.start_time
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            seconds = int(uptime % 60)
            
            logging.info(f"Статистика: Время работы: {hours:02d}:{minutes:02d}:{seconds:02d}, "
                        f"Карт обработано: {self.cards_processed}, Ошибок: {self.errors_count}")

    def run(self):
        if not self.setup():
            logging.error("Не удалось инициализировать демон")
            sys.exit(1)
            
        self.running = True
        self.start_time = time.time()
        logging.info("Демон запущен")
        
        try:
            while self.running:
                try:
                    card_number = self.reader.read_card()
                    if card_number:
                        retry_count = 0
                        success = False
                        
                        while retry_count < 5 and not success:
                            if self.db.save_card(card_number):
                                self.cards_processed += 1
                                success = True
                                break
                            retry_count += 1
                            time.sleep(1)
                        
                        if not success:
                            self.errors_count += 1
                            logging.error(f"Не удалось сохранить карту {card_number} после 5 попыток")
                    
                    # Логирование статистики каждые 100 карт или каждые 10 минут
                    if (self.cards_processed > 0 and self.cards_processed % 100 == 0) or \
                       (time.time() - self.start_time) % 600 < 0.1:
                        self.log_statistics()
                    
                    time.sleep(0.1)  # Небольшая задержка для снижения нагрузки на CPU
                    
                except Exception as e:
                    self.errors_count += 1
                    logging.error(f"Ошибка в основном цикле: {e}")
                    time.sleep(1)  # Пауза перед повторной попыткой
                
        except KeyboardInterrupt:
            logging.info("Получен сигнал завершения")
        except Exception as e:
            logging.error(f"Критическая ошибка: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Корректное завершение работы демона"""
        try:
            self.log_statistics()
            
            if self.reader:
                self.reader.cleanup()
            
            if self.db:
                del self.db
            
            logging.info("Демон остановлен")
        except Exception as e:
            logging.error(f"Ошибка при завершении работы: {e}")

def main():
    daemon = WGDaemon()
    
    if len(sys.argv) != 2 or sys.argv[1] not in ['start', 'stop', 'restart', 'status']:
        print("Использование: python wg_daemon.py [start|stop|restart|status]")
        sys.exit(1)

    if sys.argv[1] == 'status':
        if os.path.exists(daemon.pid_file):
            try:
                with open(daemon.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)  # Проверяем существование процесса
                print(f"Демон запущен (PID: {pid})")
            except (ProcessLookupError, ValueError):
                print("Демон не запущен (PID файл устарел)")
                if os.path.exists(daemon.pid_file):
                    os.remove(daemon.pid_file)
        else:
            print("Демон не запущен")
        sys.exit(0)

    if sys.argv[1] == 'stop':
        if os.path.exists(daemon.pid_file):
            try:
                with open(daemon.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, 15)  # SIGTERM
                print("Демон остановлен")
            except ProcessLookupError:
                print("Демон не запущен")
            finally:
                if os.path.exists(daemon.pid_file):
                    os.remove(daemon.pid_file)
        else:
            print("Демон не запущен")
        sys.exit(0)

    if sys.argv[1] == 'restart':
        if os.path.exists(daemon.pid_file):
            try:
                with open(daemon.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, 15)
                time.sleep(2)
            except ProcessLookupError:
                pass

    daemonize = Daemonize(
        app="wg_daemon",
        pid=daemon.pid_file,
        action=daemon.run,
        foreground=False
    )
    daemonize.start()

if __name__ == "__main__":
    main() 