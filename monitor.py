#!/usr/bin/env python3
"""
Скрипт мониторинга RFID Reader Service
Проверяет состояние сервиса, базы данных и логи
"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database import Database

load_dotenv()

class ServiceMonitor:
    def __init__(self):
        self.service_name = "rfid-reader.service"
        self.log_dir = os.getenv('LOG_DIR', './logs')
        self.db = None
        
    def check_service_status(self):
        """Проверка статуса systemd сервиса"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', self.service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip() == 'active'
        except Exception as e:
            print(f"Ошибка проверки статуса сервиса: {e}")
            return False
    
    def check_service_logs(self):
        """Проверка последних логов сервиса"""
        try:
            # Проверяем логи за последние 5 минут
            result = subprocess.run([
                'journalctl', '-u', self.service_name, 
                '--since', '5 minutes ago',
                '--no-pager'
            ], capture_output=True, text=True, timeout=10)
            
            if result.stdout.strip():
                return True, result.stdout
            else:
                return False, "Нет логов за последние 5 минут"
        except Exception as e:
            return False, f"Ошибка чтения логов: {e}"
    
    def check_database_connection(self):
        """Проверка подключения к базе данных"""
        try:
            self.db = Database()
            if self.db.test_connection():
                return True, "Подключение к БД успешно"
            else:
                return False, "Не удалось подключиться к БД"
        except Exception as e:
            return False, f"Ошибка подключения к БД: {e}"
    
    def check_recent_activity(self):
        """Проверка активности за последние 10 минут"""
        try:
            if not self.db:
                self.db = Database()
            
            cursor = self.db.connection.cursor()
            ten_minutes_ago = int(time.time()) - 600
            
            query = "SELECT COUNT(*) FROM pass WHERE time > %s"
            cursor.execute(query, (ten_minutes_ago,))
            count = cursor.fetchone()[0]
            cursor.close()
            
            if count > 0:
                return True, f"Активность обнаружена: {count} записей за 10 минут"
            else:
                return False, "Нет активности за последние 10 минут"
        except Exception as e:
            return False, f"Ошибка проверки активности: {e}"
    
    def check_log_file_size(self):
        """Проверка размера файла логов"""
        log_file = os.path.join(self.log_dir, 'wg_daemon.log')
        if os.path.exists(log_file):
            size_mb = os.path.getsize(log_file) / (1024 * 1024)
            if size_mb > 100:  # Больше 100MB
                return False, f"Файл логов слишком большой: {size_mb:.1f}MB"
            else:
                return True, f"Размер логов: {size_mb:.1f}MB"
        else:
            return False, "Файл логов не найден"
    
    def run_full_check(self):
        """Полная проверка системы"""
        print("=== Мониторинг RFID Reader Service ===")
        print(f"Время проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        checks = [
            ("Статус сервиса", self.check_service_status),
            ("Логи сервиса", self.check_service_logs),
            ("Подключение к БД", self.check_database_connection),
            ("Активность", self.check_recent_activity),
            ("Размер логов", self.check_log_file_size)
        ]
        
        all_good = True
        
        for check_name, check_func in checks:
            try:
                if check_name == "Логи сервиса":
                    status, message = check_func()
                    print(f"✓ {check_name}: {'OK' if status else 'WARNING'}")
                    if not status:
                        print(f"  {message}")
                else:
                    status, message = check_func()
                    print(f"{'✓' if status else '✗'} {check_name}: {message}")
                    if not status:
                        all_good = False
            except Exception as e:
                print(f"✗ {check_name}: Ошибка - {e}")
                all_good = False
        
        print()
        if all_good:
            print("✓ Все проверки пройдены успешно")
            return 0
        else:
            print("✗ Обнаружены проблемы")
            return 1

def main():
    monitor = ServiceMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        # Непрерывный мониторинг
        print("Запуск непрерывного мониторинга (Ctrl+C для остановки)...")
        while True:
            monitor.run_full_check()
            print("\n" + "="*50 + "\n")
            time.sleep(60)  # Проверка каждую минуту
    else:
        # Однократная проверка
        return monitor.run_full_check()

if __name__ == "__main__":
    sys.exit(main()) 