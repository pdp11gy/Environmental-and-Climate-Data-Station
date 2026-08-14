from machine import Pin, I2C
import time
# MBE680,SDA --> PICO GPIO0,PIN 1 
# MBE680,SCL --> PICO GPIO1,PIN 2
i2c = I2C(0, scl=Pin(1), sda=Pin(0))
print(i2c.scan())
# Ergebnis: [119]