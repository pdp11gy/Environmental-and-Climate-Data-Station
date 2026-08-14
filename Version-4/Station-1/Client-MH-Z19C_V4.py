#  New client/server version with additional Raspberry Pi Zero W
#  Typical data format: b'\xff\x86\x05!?\x00\x00\x00\x15'
#  Project reference with ChatGPT: CHAPDP11GY-ENV-PICO-2025
#  https://pdp11gy.com/Climatestation.html
#             www.pdp11gy.com   E-mail: info@pdp11gy.com
#  Version-4 @ Station-1
# -------------------------------------------------------------
from micropython import const
import framebuf       
from machine import Pin, I2C
from machine import UART, Pin
from ssd1306 import SSD1306_I2C
import network
import urequests
import time
import machine
#
# --------- CO2 Sensor Setup (MH-Z19C) ---------
uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
REQUEST_CO2 = b'\xFF\x01\x86\x00\x00\x00\x00\x00\x79'
#
led = machine.Pin("LED", machine.Pin.OUT)
#
# --------- OLED Setup ---------
# SSD1306-Treiber muss im selben Skript sein (wie vorher)
# I2C1 auf GP14=SDA, GP15=SCL
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)
#
SERVER = "http://192.168.178.80:5000/data"  # My Station 1
#SERVER = "http://192.168.178.72:5000/data"   # My Station 2
#
# ---------------------------------------------------------
# WLAN Daten + Power-Up
# ---------------------------------------------------------
SSID = "Dein WLAN-Name"
PW   = "Dein WLAN-Password"
#
time.sleep(2)     # Power-Up
timeout = 10
wlan = network.WLAN(network.STA_IF)
wlan.active(False)
time.sleep(1)
wlan.active(True)
wlan.connect(SSID, PW)
oled.text("Verbinde WLAN", 0, 16)
oled.show()
while not wlan.isconnected() and timeout > 0:
    time.sleep(1)
    timeout -= 1
if not wlan.isconnected():
    oled.text("  WLAN failed ", 0, 28)
    oled.text(" Reset in 5 Sec",0, 40)
    oled.show()
    time.sleep(5)
    import machine
    machine.reset()
oled.text("    WLAN ok", 0, 38)
oled.show()
time.sleep(2)
#
#
def send_co2(co2, temp):
    try:
        data = {
            "station": "station1",
            "sensor": "co2",
            "co2": co2,
            "temp": temp,
            "status": status
        }
        r = urequests.post(SERVER, json=data)
        r.close()
    except Exception as e:
        print("Sendefehler:", e)
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
#
# --------- Fehlerzähler ---------
error_count = 0
# --------- Hauptloop ---------
led.value(0)
while True:
    co2, temp, status = read_co2()
    oled.fill(0)
    if co2 is not None:
        oled.text("CO2   MH-Z19C", 0, 0)
        oled.text("CO2: {} ppm".format(co2), 0, 20)
        oled.text("Temp: {} C".format(temp), 0, 38)
        oled.show()
        #oled.text("Status: {}".format(status), 0, 48)
        #print("CO2: {} ppm  Temp: {} C  Status: {}".format(co2, temp, status))
        #---------------------------!
        #print("Sende CO2 an Server:", co2)
        send_co2(co2, temp)
        #---------------------------!
        led.toggle()   # Zustand umschalten
        time.sleep(0.2)
        led.toggle()   # Zustand umschalten
        time.sleep(0.2)
        led.toggle()   # Zustand umschalten
        time.sleep(0.2)
        led.toggle()   # Zustand umschalten
    else:
        error_count += 1
        oled.text("Warte auf Daten...", 0, 16)
        oled.text("Error-Count: {} ".format(error_count), 0, 38)
        oled.show()
        if error_count > 5:
            oled.fill(0)
            oled.text(" Reset in 2 Sec",0, 40)
            oled.show()
            time.sleep(2)
            machine.reset()
    #
    time.sleep(5)
    