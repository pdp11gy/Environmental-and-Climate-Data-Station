from machine import Pin, I2C
from time import sleep
import bmp280
from ssd1306 import SSD1306_I2C
#
i2c = I2C(0, scl=Pin(1), sda=Pin(0))
bmp = bmp280.BMP280(i2c, addr=0x76)
#
#
# BMP280 initialisieren (Adresse 0x76)
bmp = bmp280.BMP280(i2c)
#bmp = BMP280(bus)

while True:
    temp = bmp.temperature
    pressure = bmp.pressure / 100  # hPa
    print("Temp:", temp, "°C")
    print("Luftdruck:", pressure, "hPa")
    print("--------------------------")
    time.sleep(1)
