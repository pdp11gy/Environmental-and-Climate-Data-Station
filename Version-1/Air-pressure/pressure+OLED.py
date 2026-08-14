# Sensor-test, BMP280. Required library bmp280.py
# Data display on OLED SSD1306
#
from machine import Pin, I2C
from time import sleep
import bmp280
from ssd1306 import SSD1306_I2C
#
# I2C1 auf GP14 (SDA) und GP15 (SCL)
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)

# BMP280 initialisieren
bmp = bmp280.BMP280(i2c, addr=0x76)

# OLED initialisieren (128x64)
oled = SSD1306_I2C(128, 64, i2c)

while True:
    temp = bmp.temperature        # °C
    pressure = bmp.pressure       # Pa → hPa
    pressure_hpa = int(pressure / 100)
    
    print("Temp:", temp, "°C")
    print("Luftdruck:", pressure_hpa, "hPa")
    print("--------------------------")
    
    oled.fill(0)
    oled.text("BMP280 Sensor", 0, 0)
    oled.text(f"Temp: {temp:.1f} C", 0, 20)
    oled.text(f"Press: {pressure_hpa:} hPa", 0, 40)
    oled.show()
    
    sleep(1)
