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

    def read_card(self):
        try:
            card_number = 0
            bit_count = 0

            for _ in range(26):
                data0 = GPIO.input(self.data0_pin)
                data1 = GPIO.input(self.data1_pin)

                # Ждем начала передачи данных
                while data0 == 1 and data1 == 1:
                    data0 = GPIO.input(self.data0_pin)
                    data1 = GPIO.input(self.data1_pin)
                    time.sleep(0.0001)

                card_number = card_number << 1

                if data1 == 1:
                    card_number = card_number | 0x01
                bit_count += 1

                # Ждем окончания передачи бита
                while data0 == 0 or data1 == 0:
                    data0 = GPIO.input(self.data0_pin)
                    data1 = GPIO.input(self.data1_pin)

            # Обработка полученного номера карты
            card_number = card_number >> 1
            card_number = card_number & 0x00ffffff

            logging.info(f"Прочитана карта: {card_number}")
            return card_number

        except Exception as e:
            logging.error(f"Ошибка чтения карты: {e}")
            return None

    def cleanup(self):
        GPIO.cleanup()
        logging.info("GPIO очищен") 