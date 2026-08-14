# -------------------------------------------------------------
#  Feinstaub+OLED.py based on Raspberry Pi Pico W
#  SDS011 particulate matter sensor + OLED
#  Version 4.1 — stable UART parser, stable sockets, and
#  Typical data format b'\xaa\xc0\x10\x00$\x00\x170{\xab'
#  Project reference PDP11GY-ENV-PICO-2025
#  https://pdp11gy.com/Climatestation.html
#             www.pdp11gy.com   E-mail: info@pdp11gy.com
# -------------------------------------------------------------
from micropython import const
import framebuf
from machine import Pin, I2C, UART
from ssd1306 import SSD1306_I2C
import time
#
uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
#
# --------- SDS011 – Profi Parser ---------
def read_sds011():
    while uart0.any():
        b = uart0.read(1)
        if not b:
            return None, None, False        
        # Startbyte suchen
        if b[0] == 0xAA:
            frame = b + uart0.read(9)
            if len(frame) == 10:
                if frame[1] == 0xC0 and frame[9] == 0xAB:
                    pm25 = (frame[3]*256 + frame[2]) / 10.0
                    pm10 = (frame[5]*256 + frame[4]) / 10.0
                    return pm25, pm10, True
    return None, None, False
# --------- OLED Setup ---------
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)
#
# --------- Fehlerzähler ---------
error_count = 0
#
# --------- Hauptloop ---------
while True:
    pm25, pm10, ok = read_sds011()
    oled.fill(0)
    if ok:
        error_count = 0
        oled.text("Feinstaub SDS011", 0, 0)
        oled.text("PM2.5: {:.1f}".format(pm25), 0, 16)
        oled.text("PM10 : {:.1f}".format(pm10), 0, 32)
        print("PM2.5: {:.1f}  PM10: {:.1f}".format(pm25, pm10))
    else:
        oled.text("Warte auf Daten...", 0, 16)
        error_count += 1
        print("Fehler/kein Frame ({})".format(error_count))

    oled.show()
    time.sleep(2)
