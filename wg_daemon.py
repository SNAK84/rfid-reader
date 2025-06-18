#!/usr/bin/env python3
import os
import sys
import time
import logging
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class WGDaemon:
    def __init__(self):
        self.pid_file = os.getenv('PID_FILE')
        self.db = None
        self.reader = None

    def setup(self):
        try:
            self.db = Database()
            self.reader = RFIDReader()
            logging.info("Демон успешно инициализирован")
        except Exception as e:
            logging.error(f"Ошибка инициализации демона: {e}")
            sys.exit(1)

    def run(self):
        self.setup()
        logging.info("Демон запущен")
        
        try:
            while True:
                card_number = self.reader.read_card()
                if card_number:
                    retry_count = 0
                    while retry_count < 5:
                        if self.db.save_card(card_number):
                            break
                        retry_count += 1
                        time.sleep(1)
                
                time.sleep(0.1)  # Небольшая задержка для снижения нагрузки на CPU
                
        except KeyboardInterrupt:
            logging.info("Получен сигнал завершения")
        except Exception as e:
            logging.error(f"Критическая ошибка: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        if self.reader:
            self.reader.cleanup()
        logging.info("Демон остановлен")

def main():
    daemon = WGDaemon()
    
    if len(sys.argv) != 2 or sys.argv[1] not in ['start', 'stop', 'restart']:
        print("Использование: python wg_daemon.py [start|stop|restart]")
        sys.exit(1)

    if sys.argv[1] == 'stop':
        if os.path.exists(daemon.pid_file):
            with open(daemon.pid_file, 'r') as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, 15)  # SIGTERM
                print("Демон остановлен")
            except ProcessLookupError:
                print("Демон не запущен")
            finally:
                if os.path.exists(daemon.pid_file):
                    os.remove(daemon.pid_file)
        sys.exit(0)

    if sys.argv[1] == 'restart':
        if os.path.exists(daemon.pid_file):
            with open(daemon.pid_file, 'r') as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, 15)
                time.sleep(1)
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