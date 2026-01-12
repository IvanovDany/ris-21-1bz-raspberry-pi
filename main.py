# -*- coding: utf-8 -*-

import os
import time
import logging
import spidev
import RPi.GPIO as GPIO

# ==========================================================
#                 КОНСТАНТЫ И НАСТРОЙКИ
# ==========================================================

SPI_BUS = 0
SPI_DEVICE = 0
ADC_CHANNEL = 0

LCD_WIDTH = 16
LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0

# GPIO пины LCD (BOARD numbering)
LCD_RS = 15
LCD_E = 16
LCD_D4 = 7
LCD_D5 = 11
LCD_D6 = 12
LCD_D7 = 13

# Задержки для LCD
E_PULSE = 0.0005
E_DELAY = 0.0005

# Путь для логов
LOG_DIR = r"C:\Users\danii\Documents\ProteusProjects\ris-21-1bz-raspberry-pi"
LOG_FILE = "temperature_log.txt"

# ==========================================================
#                        ЛОГИРОВАНИЕ
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, LOG_FILE)),
        logging.StreamHandler()
    ]
)

# ==========================================================
#                        КЛАСС LCD
# ==========================================================

class LCD:
    """
    Класс для управления LCD 16x2 в 4-битном режиме
    """

    def __init__(self, rs, e, d4, d5, d6, d7):
        self.rs = rs
        self.e = e
        self.d4 = d4
        self.d5 = d5
        self.d6 = d6
        self.d7 = d7

        GPIO.setup([rs, e, d4, d5, d6, d7], GPIO.OUT)
        self.init()

    def init(self):
        self._write_byte(0x33, False)
        self._write_byte(0x32, False)
        self._write_byte(0x06, False)
        self._write_byte(0x0C, False)
        self._write_byte(0x28, False)
        self.clear()

    def clear(self):
        self._write_byte(0x01, False)
        time.sleep(E_DELAY)

    def display(self, message, line):
        message = message.ljust(LCD_WIDTH)
        self._write_byte(line, False)

        for char in message:
            self._write_byte(ord(char), True)

    def _toggle_enable(self):
        time.sleep(E_DELAY)
        GPIO.output(self.e, True)
        time.sleep(E_PULSE)
        GPIO.output(self.e, False)
        time.sleep(E_DELAY)

    def _write_byte(self, bits, mode):
        GPIO.output(self.rs, mode)

        for pin in [self.d4, self.d5, self.d6, self.d7]:
            GPIO.output(pin, False)

        if bits & 0x10:
            GPIO.output(self.d4, True)
        if bits & 0x20:
            GPIO.output(self.d5, True)
        if bits & 0x40:
            GPIO.output(self.d6, True)
        if bits & 0x80:
            GPIO.output(self.d7, True)

        self._toggle_enable()

        for pin in [self.d4, self.d5, self.d6, self.d7]:
            GPIO.output(pin, False)

        if bits & 0x01:
            GPIO.output(self.d4, True)
        if bits & 0x02:
            GPIO.output(self.d5, True)
        if bits & 0x04:
            GPIO.output(self.d6, True)
        if bits & 0x08:
            GPIO.output(self.d7, True)

        self._toggle_enable()

# ==========================================================
#                  SPI и MCP3208
# ==========================================================

def init_spi():
    try:
        spi = spidev.SpiDev()
        spi.open(SPI_BUS, SPI_DEVICE)
        return spi
    except Exception as e:
        logging.critical("Ошибка открытия SPI: %s", e)
        raise


def read_adc(spi, channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((adc[1] & 3) << 8) + adc[2]


def convert_temperature(adc_value, decimals=2):
    voltage = (adc_value * 3.3) / 1023.0
    temperature = voltage * 100
    return round(temperature, decimals)

# ==========================================================
#                        MAIN
# ==========================================================

def main():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    lcd = LCD(LCD_RS, LCD_E, LCD_D4, LCD_D5, LCD_D6, LCD_D7)
    spi = init_spi()

    lcd.display("Welcome!", LCD_LINE_1)
    time.sleep(2)
    lcd.clear()

    logging.info("App started")

    try:
        while True:
            adc_value = read_adc(spi, ADC_CHANNEL)
            temperature = convert_temperature(adc_value)

            lcd.display("Temperature", LCD_LINE_1)
            lcd.display(f"{temperature:.2f} C", LCD_LINE_2)

            logging.info("Temperature: %.2f C", temperature)
            time.sleep(60)

    except KeyboardInterrupt:
        logging.info("Program stopped")

    finally:
        lcd.clear()
        GPIO.cleanup()
        spi.close()
        logging.info("GPIO cleaned and SPI closed")


if __name__ == "__main__":
    main()
