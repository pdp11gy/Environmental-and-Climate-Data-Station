#  New client/server version with additional Raspberry Pi Zero W support
#  Project reference with ChatGPT: CHAPDP11GY-ENV-PICO-2025
#  https://pdp11gy.com/Climatestation.html
#             www.pdp11gy.com   E-mail: info@pdp11gy.com
#  BME680 Sensor: Version-4 @ Station-2
# -------------------------------------------------------------
from machine import UART, Pin, I2C
from ssd1306 import SSD1306_I2C
import network
import urequests
import time
import machine
import bme680
#
#--------------I2C Setup ---------
# MBE680,SDA --> PICO GPIO0,PIN 1 
# MBE680,SCL --> PICO GPIO1,PIN 2
i2c = I2C(0, scl=Pin(1), sda=Pin(0))
sensor = bme680.BME680_I2C(i2c, address=0x77)
#
# --------- OLED Setup ---------
# SSD1306-Treiber muss im selben Skript sein (wie vorher)
# I2C1 auf GP14=SDA, GP15=SCL
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)
#
led = machine.Pin("LED", machine.Pin.OUT)
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
def send_bme680(temperature, humidity, pressure):
    try:        
        data = {
            "station": "station2",
            "sensor": "bme680",
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "pressure": round(pressure, 1)
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
# -------------------------------
# Hauptloop
# -------------------------------
led.value(0)
OFFSET = 5.5                 # Korrekturwert
count = 5                    # Nur jede 5te messung wird gesendet
while True:
    temp = sensor.temperature - OFFSET
    hum = sensor.humidity
    press = sensor.pressure
    oled.fill(0)
    oled.text("BME680 Sensor", 0, 0)
    oled.text("Temp:  {:.1f}C".format(temp), 0, 20)
    oled.text("Hum:   {:.1f}%".format(hum), 0, 37)
    oled.text("Press: {:.1f}hPa".format(press), 0, 53)
    oled.show()
    #---------------------------!
    if count > 0:
        count -= 1
    else:
        count=5
        send_bme680(temp, hum, press)
        led.toggle()   # Zustand umschalten
        time.sleep(0.2)
        led.toggle()   # Zustand umschalten
        time.sleep(0.2)
        led.toggle()   # Zustand umschalten
        time.sleep(0.2)
        led.toggle()   # Zustand umschalten
        #
        #---------------------------!
        time.sleep(0.1)
# Ende Hauptloop
