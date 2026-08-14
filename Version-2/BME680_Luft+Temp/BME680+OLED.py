# Sensor BME680 + OLED display
#
from machine import I2C, Pin
from ssd1306 import SSD1306_I2C
import bme680
# MBE680,SDA --> PICO GPIO0,PIN 1 
# MBE680,SCL --> PICO GPIO1,PIN 2
i2c = I2C(0, scl=Pin(1), sda=Pin(0))
sensor = bme680.BME680_I2C(i2c, address=0x77)
#
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)
#
while True:
    #sensor = bme680.BME680_I2C(i2c, address=0x77)
    print("Temp:", sensor.temperature)
    print("Humidity:", sensor.humidity)
    print("Pressure:", sensor.pressure)
    print("Gas:", sensor.gas)
    print("-------------------")
    # OLED löschen
    oled.fill(0)
    oled.text("BME680 Sensor", 0, 0)
    oled.text("Temp:  {:.1f}C".format(sensor.temperature), 0, 22)
    oled.text("Hum:   {:.1f}%".format(sensor.humidity), 0, 39)
    oled.text("Press: {:.1f}hPa".format(sensor.pressure), 0, 55)
    oled.show()
