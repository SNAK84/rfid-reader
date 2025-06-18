import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging

load_dotenv()

class Database:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME')
            )
            logging.info("Успешное подключение к базе данных")
        except Error as e:
            logging.error(f"Ошибка подключения к базе данных: {e}")
            raise

    def save_card(self, card_number):
        if not self.connection or not self.connection.is_connected():
            self.connect()

        try:
            cursor = self.connection.cursor()
            query = "INSERT INTO pass (time, card) VALUES (%s, %s)"
            cursor.execute(query, (int(time.time()), card_number))
            self.connection.commit()
            logging.info(f"Карта {card_number} успешно сохранена")
            return True
        except Error as e:
            logging.error(f"Ошибка сохранения карты: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def __del__(self):
        if self.connection and self.connection.is_connected():
            self.connection.close() 