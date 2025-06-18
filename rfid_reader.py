import RPi.GPIO as GPIO
import time
import os
from dotenv import load_dotenv
import logging

load_dotenv()

class RFIDReader:
    def __init__(self):
        self.data0_pin = int(os.getenv('DATA0_PIN'))
        self.data1_pin = int(os.getenv('DATA1_PIN'))
        self.setup_gpio()

    def setup_gpio(self):
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.data0_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.data1_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            logging.info("GPIO успешно настроен")
        except Exception as e:
            logging.error(f"Ошибка настройки GPIO: {e}")
            raise

    def validate_card_number(self, card_number):
        """Валидация номера карты"""
        if card_number is None:
            return False
        
        # Проверяем, что номер карты в разумных пределах
        if card_number < 1 or card_number > 0x00ffffff:
            logging.warning(f"Недопустимый номер карты: {card_number}")
            return False
        
        # Проверяем, что номер не равен 0
        if card_number == 0:
            logging.warning("Получен нулевой номер карты")
            return False
            
        return True

    def read_card(self):
        try:
            card_number = 0
            bit_count = 0
            timeout_counter = 0
            max_timeout = 1000  # Максимальное время ожидания

            for _ in range(26):
                data0 = GPIO.input(self.data0_pin)
                data1 = GPIO.input(self.data1_pin)

                # Ждем начала передачи данных с таймаутом
                timeout_counter = 0
                while data0 == 1 and data1 == 1:
                    data0 = GPIO.input(self.data0_pin)
                    data1 = GPIO.input(self.data1_pin)
                    time.sleep(0.0001)
                    timeout_counter += 1
                    if timeout_counter > max_timeout:
                        logging.warning("Таймаут ожидания данных карты")
                        return None

                card_number = card_number << 1

                if data1 == 1:
                    card_number = card_number | 0x01
                bit_count += 1

                # Ждем окончания передачи бита
                timeout_counter = 0
                while data0 == 0 or data1 == 0:
                    data0 = GPIO.input(self.data0_pin)
                    data1 = GPIO.input(self.data1_pin)
                    time.sleep(0.0001)
                    timeout_counter += 1
                    if timeout_counter > max_timeout:
                        logging.warning("Таймаут ожидания окончания бита")
                        return None

            # Обработка полученного номера карты
            card_number = card_number >> 1
            card_number = card_number & 0x00ffffff

            # Валидация номера карты
            if self.validate_card_number(card_number):
                logging.info(f"Прочитана карта: {card_number}")
                return card_number
            else:
                logging.warning(f"Невалидный номер карты: {card_number}")
                return None

        except Exception as e:
            logging.error(f"Ошибка чтения карты: {e}")
            return None

    def cleanup(self):
        try:
            GPIO.cleanup()
            logging.info("GPIO очищен")
        except Exception as e:
            logging.error(f"Ошибка при очистке GPIO: {e}") 