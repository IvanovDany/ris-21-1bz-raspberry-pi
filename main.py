# -*- coding: utf-8 -*-

import os				# Импортирует библиотеку для взаимодействия с операционной системой
import time			# Импортирует библиотеку для работы со временем
import spidev			# Импортирует библиотеку для работы с SPI-интерфейсом
import RPi.GPIO as GPIO	# Импортирует библиотеку для управления GPIO-пинами Raspberry Pi
import logging			# Импортирует библиотеку для ведения журнала событий

# =======================
# КОНСТАНТЫ И НАСТРОЙКИ
# =======================

SPI_BUS = 0
SPI_DEVICE = 0
ADC_CHANNEL = 0		# Канал MCP3208, к которому подключен датчик LM35

# Константы LCD
LCD_WIDTH = 16		# Максимальное количество символов на экране
LCD_LINE_1 = 0x80		# LCD RAM адрес для первой линии экрана
LCD_LINE_2 = 0xC0		# LCD RAM адрес для второй линии экрана

# Описание пинов для LCD
LCD_RS = 15
LCD_E = 16
LCD_D4 = 7
LCD_D5 = 11
LCD_D6 = 12
LCD_D7 = 13

# Задержки для работы LCD
E_PULSE = 0.0005
E_DELAY = 0.0005

# Путь к файлу логов
LOG_DIR = r"C:\Users\danii\Documents\ProteusProjects\ris-21-1bz-raspberry-pi"
LOG_FILE = "temperature_log.txt"

# Логиорвание
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, LOG_FILE)),
        logging.StreamHandler()
    ]
)

# =========
# LCD
# =========

class LCD:
    """Класс для управления LCD 16x2 в 4-битном режиме"""
    def __init__(self, rs, e, d4, d5, d6, d7):
	# Сохраняем номера GPIO пинов
        self.rs = rs
        self.e = e
        self.d4 = d4
        self.d5 = d5
        self.d6 = d6
        self.d7 = d7
	
	# Настраиваем пины как выходы
        GPIO.setup([rs, e, d4, d5, d6, d7], GPIO.OUT)
	
	# Инициализируем LCD
        self.init()

    def init(self):
        """Инициализация LCD"""
        self._write_byte(0x33, False)	# Отправка старших 4 бит
        self._write_byte(0x32, False)	# Переключение в 4-битный режим
        self._write_byte(0x06, False)	# Направление курсора
        self._write_byte(0x0C, False)	# Включение дисплея без курсора
        self._write_byte(0x28, False)	# 2 строки, шрифт 5x8
        self.clear()

    def clear(self):
        """Очистка экрана LCD"""
        self._write_byte(0x01, False)
        time.sleep(E_DELAY)

    def display(self, message, line):
        """
        Выводит строку на LCD

        message - текст
        line - LCD_LINE_1 или LCD_LINE_2
        """
        message = message.ljust(LCD_WIDTH)
        self._write_byte(line, False)
        for c in message:
            self._write_byte(ord(c), True)

    def _toggle_enable(self):
        """Формирует импульс на пине Enable"""
        time.sleep(E_DELAY)
        GPIO.output(self.e, True)
        time.sleep(E_PULSE)
        GPIO.output(self.e, False)
        time.sleep(E_DELAY)

    def _write_byte(self, bits, mode):
        """
        Отправляет байт в LCD

        bits - данные или команда
        mode - True для символа, False для команды
        """
        GPIO.output(self.rs, mode)
	
	# Старшие 4 бита
        for p in [self.d4, self.d5, self.d6, self.d7]:
            GPIO.output(p, False)
	    
        if bits & 0x10:
            GPIO.output(self.d4, True)
        if bits & 0x20:
            GPIO.output(self.d5, True)
        if bits & 0x40:
            GPIO.output(self.d6, True)
        if bits & 0x80:
            GPIO.output(self.d7, True)
        self._toggle_enable()
	
	# Младшие 4 бита
        for p in [self.d4, self.d5, self.d6, self.d7]:
            GPIO.output(p, False)
	    
        if bits & 0x01:
            GPIO.output(self.d4, True)
        if bits & 0x02:
            GPIO.output(self.d5, True)
        if bits & 0x04:
            GPIO.output(self.d6, True)
        if bits & 0x08:
            GPIO.output(self.d7, True)
        self._toggle_enable()

# ==============
# SPI и MCP3208
# ==============

def init_spi():
    """Открывает SPI интерфейс"""
    spi = spidev.SpiDev()
    spi.open(SPI_BUS, SPI_DEVICE)
    return spi

def read_adc(spi, channel):
    """
    Считывает данные с MCP3208

    channel - номер канала 0..7
    """
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((r[1] & 3) << 8) + r[2]

def convert_temperature(adc):
    """
    Преобразует значение АЦП в температуру для LM35

    LM35 выдает 10 мВ на 1 градус
    """
    voltage = (adc * 3.3) / 1023.0
    return voltage * 100

# ======
# MAIN
# ======

def main():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    lcd = LCD(LCD_RS, LCD_E, LCD_D4, LCD_D5, LCD_D6, LCD_D7)
    spi = init_spi()

    lcd.display("Welcome", LCD_LINE_1)
    time.sleep(2)
    lcd.clear()

    try:
        while True:
            adc = read_adc(spi, ADC_CHANNEL)
            temp = convert_temperature(adc)

            lcd.display("Temperature", LCD_LINE_1)
            lcd.display(f"{temp:.2f} *C", LCD_LINE_2)

            logging.info("Temp %.2f *C", temp)
            time.sleep(60)
    except KeyboardInterrupt:
        pass
    finally:
        lcd.clear()
        GPIO.cleanup()
        spi.close()

if __name__ == "__main__":
    main()
