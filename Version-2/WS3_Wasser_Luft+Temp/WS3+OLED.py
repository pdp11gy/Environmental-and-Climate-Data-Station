#         WS3, Weather module 3
# produces the following output, example:
# b'c000s000g000t076r000p000h44b09623*34\r\n'
#
from machine import UART, Pin, I2C
import time
from ssd1306 import SSD1306_I2C
# -------------------------------
# OLED INITIALISIERUNG
# -------------------------------
# I2C1 auf GP14 (SDA) und GP15 (SCL)
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
# OLED initialisieren (128x64)
oled = SSD1306_I2C(128, 64, i2c)
# -------------------------------
# UART Weather Module WS3
# WS3/TX-->UART0/Pin2(GP1) WS3/RX-->UART0/PIN1(GP0)
# -------------------------------
uart = UART(0, baudrate=9600, tx=Pin(2), rx=Pin(1))
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
        "temperature":    int(text[13:16]) / 10.0,
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

# -------------------------------
# Hauptloop
# -------------------------------
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
            print("----------------------------------------------------------------")
            print(data)
            # OLED löschen
            oled.fill(0)
            #
            # --- Erste Zeile ---
            oled.text("Temp: {:.1f}C".format(data["temperature"]), 0, 0)
            oled.text("Hum: {}%".format(data["humidity"]), 70, 0)
            #
            # --- Druck ---
            oled.text("Pres: {:.1f}hPa".format(data["pressure"]), 0, 12)
            #
            # --- Wind ---
            wtxt = wind_dir_to_text(data["wind_dir"])
            oled.text("Wind: {} {:0.1f}m/s".format(wtxt, data["wind_speed"]), 0, 24)
            oled.text("Gust: {:0.1f}".format(data["wind_gust"]), 0, 36)

            # --- Regen ---
            oled.text("RainR: {}".format(data["rain_rate"]), 0, 48)
            oled.text("RainT: {}".format(data["rain_total"]), 70, 48)

            # OLED aktualisieren
            oled.show()

        except Exception as e:
            oled.fill(0)
            oled.text("Parse Error", 0, 0)
            oled.show()

    time.sleep(0.1)

