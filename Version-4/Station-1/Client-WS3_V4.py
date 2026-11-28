# New client/server version with additional Raspberry Pi Zero W
# Produces the following output (example):
# b'c000s000g000t076r000p000h44b09623*34\r\n'
# Project reference with ChatGPT: CHAPDP11GY-ENV-PICO-2025
#  https://pdp11gy.com/Climatestation.html
#             www.pdp11gy.com   E-mail: info@pdp11gy.com
#  Version-4 @ Station-1
# -------------------------------------------------------------
from machine import UART, Pin, I2C
from ssd1306 import SSD1306_I2C
import network
import urequests
import time
import machine
#
# UART Weather Module WS3
# WS3/TX-->UART0/Pin2(GP1) WS3/RX-->UART0/PIN1(GP0)
uart = UART(0, baudrate=9600, tx=Pin(2), rx=Pin(1))
#
# --------- OLED Setup ---------
# SSD1306-Treiber muss im selben Skript sein (wie vorher)
# I2C1 auf GP14=SDA, GP15=SCL
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)
#
led = machine.Pin("LED", machine.Pin.OUT)
#
SERVER = "http://192.168.178.80:5000/data"   # My Station 1
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
# -------------------------------
# Parser für WS3 Telegramme
# -------------------------------
def parse_ws3(raw):
    text = raw.decode().strip()
    print(text)
    if len(text) < 36 or "*" not in text:
        raise ValueError("Unvollständiges Telegramm")

    return {
        "wind_dir":       int(text[1:4]),
        "wind_speed":     int(text[5:8]) / 10.0,
        "wind_gust":      int(text[9:12]) / 10.0,
        #"temperature":    int(text[13:16]) / 10.0,
        "temperature":    (int(text[13:16])-32.0)/1.8,  # Farenheit -> Celsius
        "rain_total":     int(text[17:20]),
        "rain_rate":      int(text[21:24]),
        "humidity":       int(text[25:27]),
        "pressure":       int(text[28:33]) / 10.0,
        "checksum":       text.split("*")[1]
    }

# -------------------------------
# Windrichtung als Text
# -------------------------------
def wind_dir_to_text(deg):
    dirs = [
        "N", "NO", "O", "SO",
        "S", "SW", "W", "NW"
    ]
    idx = int((deg % 360) / 45)
    return dirs[idx]
#
def send_ws3(temperature, humidity, pressure, wind_speed, wind_gust, rain_rate, rain_total):
    try:
        data = {
            "station": "station1",
            "sensor": "ws3",               # wichtig:
            "temperature": temperature,
            "humidity": humidity,
            "pressure": pressure,
            "wind_speed": wind_speed,
            "wind_gust": wind_gust,
            "rain_rate": rain_rate,
            "rain_total": rain_total
        }
        r = urequests.post(SERVER, json=data)
        r.close()
    except Exception as e:
        print("Sendefehler:", e)
#
# -------------------------------
# Hauptloop
# -------------------------------
led.value(0)
count = 5                  # Nur jede 5te messung wird gesendet
while True:
    if uart.any():
        line = uart.readline()
        if not line:
            continue

        text = line.decode().strip()

        if "*" not in text or len(text) < 36:
            continue  # unvollständig

        try:
            data = parse_ws3(line)
            #print("----------------------------------------------------------------")
            #print(data)
            # OLED löschen
            oled.fill(0)
            #
            # --- Erste Zeile ---
            oled.text("Temp:{:.1f}C".format(data["temperature"]), 0, 0)
            oled.text("Hum:{}%".format(data["humidity"]), 72, 0)
            #
            # --- Druck ---
            oled.text("Pres: {:.1f}hPa".format(data["pressure"]), 0, 12)
            #
            # --- Wind ---
            wtxt = wind_dir_to_text(data["wind_dir"])
            oled.text("Wind: {} {:0.1f}m/s".format(wtxt, data["wind_speed"]), 0, 24)
            oled.text("Gust: {:0.1f}".format(data["wind_gust"]), 0, 36)
            #
            # --- Regen ---
            oled.text("RainR: {}".format(data["rain_rate"]), 0, 48)
            oled.text("RainT: {}".format(data["rain_total"]), 70, 48)
            #
            # OLED aktualisieren
            oled.show()
            #
            #---------------------------!
            if count > 0:
                count -= 1
            else:
                count = 5
                send_ws3(
                data["temperature"],
                data["humidity"],
                data["pressure"],
                data["wind_speed"],
                data["wind_gust"],
                data["rain_rate"],
                data["rain_total"]
                )
                #---------------------------!
                led.toggle()   # Zustand umschalten
                time.sleep(0.2)
                led.toggle()   # Zustand umschalten
                time.sleep(0.2)
                led.toggle()   # Zustand umschalten
                time.sleep(0.2)
                led.toggle()   # Zustand umschalten
                #
        except Exception as e:
            oled.fill(0)
            oled.text("Parse Error", 0, 0)
            oled.show()
            #
    #time.sleep(5)
    time.sleep(0.1)
