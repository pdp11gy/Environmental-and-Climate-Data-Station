from machine import Pin, I2C
from time import sleep
import bmp280
from ssd1306 import SSD1306_I2C
#
i2c = I2C(0, scl=Pin(1), sda=Pin(0))
bmp = bmp280.BMP280(i2c, addr=0x76)
#
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)
#
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

