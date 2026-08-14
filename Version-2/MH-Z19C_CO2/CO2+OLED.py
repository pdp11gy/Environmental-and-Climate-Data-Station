# CO2 Sensor and OLED display
#
from micropython import const
import framebuf       
from machine import Pin, I2C
from machine import UART, Pin
from ssd1306 import SSD1306_I2C
import time
# --------- CO2 Sensor Setup (MH-Z19C) ---------
uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
REQUEST_CO2 = b'\xFF\x01\x86\x00\x00\x00\x00\x00\x79'
#
def co2_checksum(data):
    # Prüfsumme berechnen laut Datenblatt
    return (0xFF - (sum(data[1:8]) % 256) + 1) & 0xFF
def read_co2():
    uart0.write(REQUEST_CO2)
    time.sleep(0.1)
    if uart0.any():
        response = uart0.read(9)
        if response and len(response) == 9 and response[0] == 0xFF and response[1] == 0x86:
            if response[8] == co2_checksum(response):
                co2 = response[2] * 256 + response[3]
                temp = response[4] - 40
                status = response[5]
                return co2, temp, status
    return None, None, None

# --------- OLED Setup ---------
# SSD1306-Treiber muss im selben Skript sein (wie vorher)
# I2C1 auf GP14=SDA, GP15=SCL
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)
#time.sleep(1) 


# Clear the display first
oled.fill(0) # --------- Hauptloop ---------
while True:
    co2, temp, status = read_co2()
    oled.fill(0)
    if co2 is not None:
        oled.text("CO2 Sensor", 0, 0)
        oled.text("CO2: {} ppm".format(co2), 0, 16)
        oled.text("Temp: {} C".format(temp), 0, 32)
        oled.text("Status: {}".format(status), 0, 48)
        print("CO2: {} ppm  Temp: {} C  Status: {}".format(co2, temp, status))
    else:
        oled.text("Warte auf Daten...", 0, 16)
    oled.show()
    time.sleep(2)