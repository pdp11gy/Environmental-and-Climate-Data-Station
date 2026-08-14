# Sensor-test, BMP280. Required library bmp280.py
#
from machine import Pin, I2C
from bmp280 import *
import time
#
# I2C1 = GP14 (SDA), GP15 (SCL)
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
# BMP280 Treiber importieren
import bmp280

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
