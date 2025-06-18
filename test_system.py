#!/usr/bin/env python3
"""
Скрипт тестирования RFID Reader System
Проверяет все компоненты системы перед запуском
"""

import os
import sys
import time
import subprocess
from dotenv import load_dotenv

load_dotenv()

class SystemTester:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        
    def print_result(self, test_name, success, message=""):
        """Вывод результата теста"""
        if success:
            print(f"✅ {test_name}: PASSED")
            if message:
                print(f"   {message}")
            self.tests_passed += 1
        else:
            print(f"❌ {test_name}: FAILED")
            if message:
                print(f"   {message}")
            self.tests_failed += 1
        print()
    
    def test_python_dependencies(self):
        """Тест Python зависимостей"""
        required_packages = [
            'RPi.GPIO',
            'mysql.connector',
            'dotenv',
            'daemonize'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self.print_result(
                "Python зависимости", 
                False, 
                f"Отсутствуют пакеты: {', '.join(missing_packages)}"
            )
            return False
        else:
            self.print_result("Python зависимости", True)
            return True
    
    def test_environment_file(self):
        """Тест конфигурационного файла"""
        env_file = '.env'
        if not os.path.exists(env_file):
            self.print_result("Конфигурационный файл", False, "Файл .env не найден")
            return False
        
        required_vars = [
            'DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME',
            'DATA0_PIN', 'DATA1_PIN', 'LOG_DIR', 'PID_FILE'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.print_result(
                "Конфигурационный файл", 
                False, 
                f"Отсутствуют переменные: {', '.join(missing_vars)}"
            )
            return False
        else:
            self.print_result("Конфигурационный файл", True)
            return True
    
    def test_database_connection(self):
        """Тест подключения к базе данных"""
        try:
            from database import Database
            db = Database()
            if db.test_connection():
                self.print_result("Подключение к БД", True)
                return True
            else:
                self.print_result("Подключение к БД", False, "Тест подключения не прошел")
                return False
        except Exception as e:
            self.print_result("Подключение к БД", False, str(e))
            return False
    
    def test_gpio_access(self):
        """Тест доступа к GPIO"""
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            
            # Тестируем доступ к пинам
            data0_pin = int(os.getenv('DATA0_PIN'))
            data1_pin = int(os.getenv('DATA1_PIN'))
            
            GPIO.setup(data0_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(data1_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Читаем состояние пинов
            _ = GPIO.input(data0_pin)
            _ = GPIO.input(data1_pin)
            
            GPIO.cleanup()
            self.print_result("Доступ к GPIO", True)
            return True
        except Exception as e:
            self.print_result("Доступ к GPIO", False, str(e))
            return False
    
    def test_log_directory(self):
        """Тест директории логов"""
        log_dir = os.getenv('LOG_DIR')
        try:
            os.makedirs(log_dir, exist_ok=True)
            
            # Тест записи в лог
            test_log_file = os.path.join(log_dir, 'test.log')
            with open(test_log_file, 'w') as f:
                f.write('test')
            
            # Удаляем тестовый файл
            os.remove(test_log_file)
            
            self.print_result("Директория логов", True)
            return True
        except Exception as e:
            self.print_result("Директория логов", False, str(e))
            return False
    
    def test_pid_file_access(self):
        """Тест доступа к PID файлу"""
        pid_file = os.getenv('PID_FILE')
        try:
            # Создаем тестовый PID файл
            with open(pid_file, 'w') as f:
                f.write('12345')
            
            # Читаем PID файл
            with open(pid_file, 'r') as f:
                pid = f.read().strip()
            
            # Удаляем тестовый файл
            os.remove(pid_file)
            
            self.print_result("PID файл", True)
            return True
        except Exception as e:
            self.print_result("PID файл", False, str(e))
            return False
    
    def test_rfid_reader_class(self):
        """Тест класса RFID Reader"""
        try:
            from rfid_reader import RFIDReader
            reader = RFIDReader()
            
            # Тестируем валидацию
            assert reader.validate_card_number(12345) == True
            assert reader.validate_card_number(0) == False
            assert reader.validate_card_number(None) == False
            
            reader.cleanup()
            self.print_result("RFID Reader класс", True)
            return True
        except Exception as e:
            self.print_result("RFID Reader класс", False, str(e))
            return False
    
    def test_database_class(self):
        """Тест класса Database"""
        try:
            from database import Database
            db = Database()
            
            # Тестируем валидацию
            assert db.validate_card_data(12345) == True
            assert db.validate_card_data(0) == False
            assert db.validate_card_data(None) == False
            assert db.validate_card_data("invalid") == False
            
            self.print_result("Database класс", True)
            return True
        except Exception as e:
            self.print_result("Database класс", False, str(e))
            return False
    
    def test_systemd_service(self):
        """Тест systemd сервиса"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-enabled', 'rfid-reader.service'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.print_result("Systemd сервис", True, "Сервис включен")
                return True
            else:
                self.print_result("Systemd сервис", False, "Сервис не включен")
                return False
        except Exception as e:
            self.print_result("Systemd сервис", False, str(e))
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🧪 Тестирование RFID Reader System")
        print("=" * 50)
        print()
        
        tests = [
            ("Python зависимости", self.test_python_dependencies),
            ("Конфигурационный файл", self.test_environment_file),
            ("Подключение к БД", self.test_database_connection),
            ("Доступ к GPIO", self.test_gpio_access),
            ("Директория логов", self.test_log_directory),
            ("PID файл", self.test_pid_file_access),
            ("RFID Reader класс", self.test_rfid_reader_class),
            ("Database класс", self.test_database_class),
            ("Systemd сервис", self.test_systemd_service)
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.print_result(test_name, False, f"Неожиданная ошибка: {e}")
        
        # Итоговый результат
        print("=" * 50)
        print(f"📊 Результаты тестирования:")
        print(f"   ✅ Пройдено: {self.tests_passed}")
        print(f"   ❌ Провалено: {self.tests_failed}")
        print(f"   📈 Успешность: {self.tests_passed/(self.tests_passed+self.tests_failed)*100:.1f}%")
        
        if self.tests_failed == 0:
            print("\n🎉 Все тесты пройдены успешно! Система готова к работе.")
            return 0
        else:
            print(f"\n⚠️  Обнаружено {self.tests_failed} проблем. Исправьте их перед запуском.")
            return 1

def main():
    tester = SystemTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main()) 