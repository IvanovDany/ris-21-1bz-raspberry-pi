import spidev  # Импортирует библиотеку для работы с SPI-интерфейсом
import time    # Импортирует библиотеку для работы со временем
import os      # Импортирует библиотеку для взаимодействия с операционной системой
import RPi.GPIO as GPIO  # Импортирует библиотеку для управления GPIO-пинами Raspberry Pi
GPIO.setmode(GPIO.BOARD)  # Устанавливает режим нумерации GPIO-пинов на BOARD (физические номера пинов)
GPIO.setwarnings(False) # Отключает предупреждения GPIO

spi = spidev.SpiDev()  # Создает объект SPI
spi.open(0,0)          # Открывает SPI-порт 0, устройство (CE) 0


temp_channel  = 0 # Определяет номер канала АЦП, к которому подключен датчик температуры

# Описание пинов для LCD:

# Описание GPIO для LCD
LCD_RS = 15
LCD_E  = 16
LCD_D4 = 7
LCD_D5 = 11
LCD_D6 = 12
LCD_D7 = 13

# Констатны задержки
E_PULSE = 0.0005
E_DELAY = 0.0005
delay = 1

GPIO.setup(LCD_E, GPIO.OUT)  # E
GPIO.setup(LCD_RS, GPIO.OUT) # RS
GPIO.setup(LCD_D4, GPIO.OUT) # D4
GPIO.setup(LCD_D5, GPIO.OUT) # D5
GPIO.setup(LCD_D6, GPIO.OUT) # D6
GPIO.setup(LCD_D7, GPIO.OUT) # D7

# Константы LCD
LCD_WIDTH = 16    # Максимальное количество символов на экране
LCD_CHR = True    # Константа для передачи символьных данных на LCD
LCD_CMD = False   # Константа для передачи команд на LCD
LCD_LINE_1 = 0x80 # LCD RAM адрес для первой линии экрана
LCD_LINE_2 = 0xC0 # LCD RAM адрес для второй линии экрана

# Функция для инициализации LCD
def lcd_init():
  lcd_byte(0x33,LCD_CMD) # 110011 (Отправка старых 4 бит)
  lcd_byte(0x32,LCD_CMD) # 110010 (Отправка младших 4 бит)
  lcd_byte(0x06,LCD_CMD) # 000110 (Направление движения курсора)
  lcd_byte(0x0C,LCD_CMD) # 001100 (Включение дисплея, выключение курсора, выключение мигания)
  lcd_byte(0x28,LCD_CMD) # 101000 (Длина данных (4 бита), количество строк (2), размер шрифта (5x8 точек))
  lcd_byte(0x01,LCD_CMD) # 000001 (Очистка дисплея (очищает дисплей и устанавливает курсор в начало))
  time.sleep(E_DELAY) # Задержка после инициализации

 # Функция для преобразовывания байтовых данные в биты и отправления на порт LCD
def lcd_byte(bits, mode):
  # bits = данные
  # mode = True  для символа, False для команды
 
  GPIO.output(LCD_RS, mode) # RS
 
  # Старшие биты (Отправка старших 4 бит)
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x10==0x10:
    GPIO.output(LCD_D4, True)
  if bits&0x20==0x20:
    GPIO.output(LCD_D5, True)
  if bits&0x40==0x40:
    GPIO.output(LCD_D6, True)
  if bits&0x80==0x80:
    GPIO.output(LCD_D7, True)
 
  # Переключение пина 'Enable' (Импульс на линии Enable для фиксации данных)
  lcd_toggle_enable()
 
  # Младшие биты (отправка младших 4 бит)
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x01==0x01:
    GPIO.output(LCD_D4, True)
  if bits&0x02==0x02:
    GPIO.output(LCD_D5, True)
  if bits&0x04==0x04:
    GPIO.output(LCD_D6, True)
  if bits&0x08==0x08:
    GPIO.output(LCD_D7, True)
 
 # Переключение пина 'Enable' (Еще один импульс для фиксации младших 4 бит)
  lcd_toggle_enable()

 # Функция для переключения пина Enable
def lcd_toggle_enable():
  time.sleep(E_DELAY)
  GPIO.output(LCD_E, True)
  time.sleep(E_PULSE)
  GPIO.output(LCD_E, False)
  time.sleep(E_DELAY)

 # Функция для вывода сообщения на LCD
def lcd_string(message,line):
  message = message.ljust(LCD_WIDTH," ") # Дополняет строку пробелами до ширины LCD
 
  lcd_byte(line, LCD_CMD) # Отправляет команду для установки курсора на нужную строку
 
  for i in range(LCD_WIDTH):
    lcd_byte(ord(message[i]),LCD_CHR) # Отправляет каждый символ строки на LCD



 
# Функция для чтения данных SPI с чипа MCP3008
# Канал должен быть целым числом от 0 до 7
def ReadChannel(channel):
  adc = spi.xfer2([1,(8+channel)<<4,0]) # [1, (8+channel)<<4, 0] - формат команды для MCP3008
  data = ((adc[1]&3) << 8) + adc[2] # Обрабатывает полученные байты для получения 10-битного значения АЦП
  return data

 
# Функция для расчета температуры из данных TMP36, округленной до указанного количества десятичных знаков
def ConvertTemp(data,places):
 
  # Значение АЦП
  # (знач.)  Темп.  Вольт.
  #   0       -50       0.00
  #  78       -25      0.25
  # 155        0       0.50
  # 233       25      0.75
  # 310       50      1.00
  # 465      100     1.50
  # 775      200     2.50
  # 1023     280    3.30
 
  temp = ((data * 330)/float(1023)) # Преобразует значение АЦП (0-1023) в приблизительное напряжение (0-3.3V) и затем в температур
  temp = round(temp,places)
  return temp
 
# Функция для записи температуры в файл
def log_temperature(temperature, filename="temperature_log.txt"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    home_dir = os.path.expanduser("~")
    full_path = os.path.join(home_dir, filename)
    try:
        with open(full_path, "a", encoding="utf-8") as file:
            file.write(f"{timestamp}: {temperature} *C\n")
    except IOError as e:
        print(f"Error: {e}")


# Определяет задержку между показаниями
delay = 5
lcd_init()
lcd_string("Welcome! ",LCD_LINE_1)
time.sleep(2)
while 1:
  temp_level = ReadChannel(temp_channel) 
  temp = ConvertTemp(temp_level,2)
 
  # Вывод на LCD температуры
  lcd_string("Temperature  ",LCD_LINE_1)
  lcd_string(str(temp),LCD_LINE_2)
  
  # Запись температуры в файл
  log_temperature(temp)
  
  time.sleep(1)
  