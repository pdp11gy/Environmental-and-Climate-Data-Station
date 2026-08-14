# Test program for SENSOR BMP280
# Library bmp280 is required
#
from machine import I2C, Pin
import urequests
import time
import machine
import bmp280
#
# ------- bmp280 Setup -----------
# BMP280,SDA --> PICO GPIO0,PIN 1 
# BMP280,SCL --> PICO GPIO1,PIN 2
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=10000)
bmp = bmp280.BMP280(i2c, addr=0x76)
# ---------------------------------------
# Hauptschleife
# ---------------------------------------
while True:
    try:
        # bmp280 auslesen (nicht-blockierend, mit Fehlerbehandlung)
        temp = bmp.temperature        # °C
        pressure = bmp.pressure
        pres = int(pressure / 100)
        print("Temp:", temp, "C   Pressure:", pres, "hPa")
    except Exception as e:
        print("I2C Fehlfunktion:", e)
    time.sleep(1)
