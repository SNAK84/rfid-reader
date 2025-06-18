import mysql.connector
from mysql.connector import Error
import os
import time
from dotenv import load_dotenv
import logging

load_dotenv()

class Database:
    def __init__(self):
        self.connection = None
        self.max_retries = 3
        self.retry_delay = 1
        self.connect()

    def connect(self):
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                self.connection = mysql.connector.connect(
                    host=os.getenv('DB_HOST'),
                    user=os.getenv('DB_USER'),
                    password=os.getenv('DB_PASSWORD'),
                    database=os.getenv('DB_NAME'),
                    autocommit=True,
                    charset='utf8mb4'
                )
                logging.info("Успешное подключение к базе данных")
                return
            except Error as e:
                retry_count += 1
                logging.error(f"Ошибка подключения к базе данных (попытка {retry_count}/{self.max_retries}): {e}")
                if retry_count < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    raise

    def validate_card_data(self, card_number):
        """Валидация данных карты перед сохранением"""
        if card_number is None:
            return False
        
        # Проверяем, что card_number является числом
        try:
            card_number = int(card_number)
        except (ValueError, TypeError):
            logging.warning(f"Недопустимый тип данных для номера карты: {type(card_number)}")
            return False
        
        # Проверяем диапазон
        if card_number < 1 or card_number > 0x00ffffff:
            logging.warning(f"Номер карты вне допустимого диапазона: {card_number}")
            return False
            
        return True

    def save_card(self, card_number):
        # Валидация данных
        if not self.validate_card_data(card_number):
            logging.error(f"Невалидные данные карты: {card_number}")
            return False

        # Проверка подключения
        if not self.connection or not self.connection.is_connected():
            try:
                self.connect()
            except Exception as e:
                logging.error(f"Не удалось переподключиться к базе данных: {e}")
                return False

        retry_count = 0
        while retry_count < self.max_retries:
            try:
                cursor = self.connection.cursor()
                query = "INSERT INTO pass (time, card) VALUES (%s, %s)"
                current_time = int(time.time())
                cursor.execute(query, (current_time, str(card_number)))
                self.connection.commit()
                logging.info(f"Карта {card_number} успешно сохранена в {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))}")
                return True
            except Error as e:
                retry_count += 1
                logging.error(f"Ошибка сохранения карты (попытка {retry_count}/{self.max_retries}): {e}")
                if retry_count < self.max_retries:
                    time.sleep(self.retry_delay)
                    # Попытка переподключения
                    try:
                        self.connect()
                    except:
                        pass
            finally:
                if 'cursor' in locals():
                    cursor.close()
        
        logging.error(f"Не удалось сохранить карту {card_number} после {self.max_retries} попыток")
        return False

    def test_connection(self):
        """Тест подключения к базе данных"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            logging.info("Тест подключения к базе данных успешен")
            return True
        except Exception as e:
            logging.error(f"Тест подключения к базе данных не удался: {e}")
            return False

    def __del__(self):
        if self.connection and self.connection.is_connected():
            self.connection.close() 