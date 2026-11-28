#  New client/server version with additional Raspberry Pi Zero W
#                 SDS011 particulate matter sensor
#  Typical data format b'\xaa\xc0\x10\x00$\x00\x170{\xab'
#  Project reference with ChatGPT: CHAPDP11GY-ENV-PICO-2025
#  https://pdp11gy.com/Climatestation.html
#             www.pdp11gy.com   E-mail: info@pdp11gy.com
#  Sensor SDS011:  Version-4 @ Station-2
# -------------------------------------------------------------
from micropython import const
import framebuf
from machine import Pin, I2C, UART
from ssd1306 import SSD1306_I2C
import network
import urequests
import time
import machine
#
# Feinstaub Sensor SDS011
uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
#
led = machine.Pin("LED", machine.Pin.OUT)
#
# --------- OLED Setup ---------
# SSD1306-Treiber muss im selben Skript sein (wie vorher)
# I2C1 auf GP14=SDA, GP15=SCL
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)
#
SERVER1 = "http://192.168.178.80:5000/data"   # My Station 1
SERVER2 = "http://192.168.178.72:5000/data"   # My Station 2
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
def send_to_server(url, data):
    try:
        r = urequests.post(url, json=data, timeout=3)
        r.close()
        return True
    except Exception as e:
        print("Sendefehler:", e)
        return False
#
def send_feinstaub(co2, temp):
    try:
        data = {
            "station": "station2",
            "sensor": "Feinstaub",
            "pm25":  pm25,
            "pm10": pm10
        }
        server1_ok = send_to_server(SERVER1, data)
        if server1_ok:
            #print("Server1 online")
            # zusätzlich zu Server2
            send_to_server(SERVER2, data)
        else:
            #print("Server1 offline")
            # nur Server2
            send_to_server(SERVER2, data)                
    except Exception as e:
        print("Sendefehler:", e)
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
#
# --------- Fehlerzähler ---------
error_count = 0
#
# --------- Hauptloop ---------
led.value(0)
while True:
    pm25, pm10, ok = read_sds011()
    oled.fill(0)
    if ok:
        error_count = 0
        oled.text("Feinstaub SDS011", 0, 3)
        oled.text("PM2.5: {:.1f} ug".format(pm25), 0, 23)
        oled.text("PM10 : {:.1f} ug".format(pm10), 0, 41)
        #print("PM2.5: {:.1f}  PM10: {:.1f}".format(pm25, pm10))
        #---------------------------!
        #print("Sende FEINSTAUB  an Server:", pm25,pm10)
        send_feinstaub(pm25, pm10)
        #---------------------------!
    else:
        oled.text("Warte auf Daten...", 0, 16)
        error_count += 1
        print("Fehler/kein Frame ({})".format(error_count))

    oled.show()
    #
    led.toggle()   # Zustand umschalten
    time.sleep(0.2)
    led.toggle()   # Zustand umschalten
    time.sleep(0.2)
    led.toggle()   # Zustand umschalten
    time.sleep(0.2)
    led.toggle()   # Zustand umschalten
    #
    time.sleep(5)
