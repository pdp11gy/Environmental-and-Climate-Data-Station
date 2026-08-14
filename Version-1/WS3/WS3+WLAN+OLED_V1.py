# -------------------------------------------------------------
#  WS3+WLAN+OLED_V1.py  based on Raspberry PI PICO w
#  WS3 Wettermodul + OLED + WLAN + Webserver 
#  Version 1 — stabiler UART-Parser, stabile Sockets und
#  Debug Mode: http://<IP-Adresse>/debug?on=false/true
#  Typisches Daten-Format c090s000g000t072r000p000h48b09400*36
#  Projekt Referenz PDP11GY-ENV-PICO-2025
#  https://www.pdp11gy.com/dokumente/WetterstationPLUS.zip
# -------------------------------------------------------------
import time
import network
import socket
from machine import UART, Pin, I2C
from ssd1306 import SSD1306_I2C
#
# ------------------------------------------------------------
#  DEBUG FLAG
DEBUG = False   # wird per Browser geändert
# ------------------------------------------------------------
#
# ------------------------------------------------------------
#  CLEANUP BEIM START — VERHINDERT ERRNO 98 NICHT FREIGEGEBEN
# ------------------------------------------------------------
def clean_start():
    try:
        wlan = network.WLAN(network.STA_IF)
        if wlan.active():
            wlan.active(False)
            time.sleep(0.3)
    except:
        pass

    try:
        s = socket.socket()
        s.close()
    except:
        pass

    time.sleep(0.3)

clean_start()
#
# ------------------------------------------------------------
# I2C + OLED
# ------------------------------------------------------------
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)
#
# ------------------------------------------------------------
# UART – WS3
# ------------------------------------------------------------
uart = UART(0, baudrate=9600, tx=Pin(2), rx=Pin(1))
#
# ------------------------------------------------------------
# WLAN SETUP
# ------------------------------------------------------------
SSID = "DEIN WLAN-Name"
PASS = "DEIN WLAN-Password"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASS)
    print("Verbinde mit WLAN...", end="")

    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.3)

    print("\nVerbunden!")
    print("IP:", wlan.ifconfig()[0])
    return wlan.ifconfig()[0]

ip = connect_wifi()

# ------------------------------------------------------------
# WS3 Parser – stabil
# ------------------------------------------------------------
def parse_ws3(line):
    text = line.decode().strip()

    if "*" not in text:
        raise ValueError("Kein Checksum-Trenner")
    if len(text) < 34:
        raise ValueError("Zu kurz")
    if not text.startswith("c"):
        raise ValueError("Kein WS3-Frame")

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

def wind_dir_to_text(deg):
    dirs = ["N", "NO", "O", "SO", "S", "SW", "W", "NW"]
    idx = int((deg % 360) / 45)
    return dirs[idx]

# ------------------------------------------------------------
# Webserver starten
# ------------------------------------------------------------
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(addr)
server.listen(1)
print("Webserver läuft → http://{}".format(ip))

# ------------------------------------------------------------
# Hauptloop
# ------------------------------------------------------------
last_data = None

while True:
    # -------------------------------
    # UART / WS3 lesen
    # -------------------------------
    if uart.any():
        raw = uart.readline()
        if raw:
            try:
                parsed = parse_ws3(raw)
                last_data = parsed

                # Debug-Ausgabe
                if DEBUG:
                    print("----------------------------------------------------------------")
                    print(raw)
                    print(parsed)
                else:
                    print(".", end="")
                #
                # OLED Ausgabe
                oled.fill(0)
                oled.text("Temp:{:.1f}C".format(parsed["temperature"]), 0, 0)
                oled.text("Hum:{}%".format(parsed["humidity"]), 0, 55)

                oled.text("Pres:{:.1f}".format(parsed["pressure"]), 0, 11)

                wtxt = wind_dir_to_text(parsed["wind_dir"])
                oled.text("Wind:{} {:.1f}".format(wtxt, parsed["wind_speed"]), 0, 22)
                oled.text("Gust:{:.1f}".format(parsed["wind_gust"]), 0, 33)

                oled.text("RainR:{}".format(parsed["rain_rate"]), 0, 44)
                oled.text("RainT:{}".format(parsed["rain_total"]), 70, 44)

                oled.show()

            except Exception as e:
                if DEBUG:
                    print("UART-Fehler:", e)

    # -------------------------------
    # Webserver requests
    # -------------------------------
    try:
        server.settimeout(0.3)
        client, addr = server.accept()
    except:
        client = None

    if client:
        req = client.recv(1024)
        req_str = req.decode("utf-8")

        # Debug toggeln per URL
        #global DEBUG
        if "/debug?on=true" in req_str:
            DEBUG = True
        elif "/debug?on=false" in req_str:
            DEBUG = False

        debug_state = "Aktiv" if DEBUG else "Inaktiv"

        # HTML generieren
        if last_data:
            html = """<html><head>
<meta http-equiv="refresh" content="5">
<title>WS3 Wetterstation</title></head><body>
<h2>WS3 Wetterstation</h2>
<meta charset="UTF-8">
<p><b>Temperatur:</b> {:.1f} °C</p>
<p><b>Luftfeuchte:</b> {}%</p>
<p><b>Wind:</b> {} {:.1f} m/s</p>
<p><b>Böen:</b> {:.1f}</p>
<p><b>Druck:</b> {:.1f} hPa</p>
<p><b>Regen Rate:</b> {}</p>
<p><b>Regen Total:</b> {}</p>

<hr>
<p><b>Debug-Modus:</b> {}</p>
<p><a href="/debug?on=true">Debug EIN</a> | 
<a href="/debug?on=false">Debug AUS</a></p>

</body></html>""".format(
                last_data["temperature"],
                last_data["humidity"],
                wind_dir_to_text(last_data["wind_dir"]),
                last_data["wind_speed"],
                last_data["wind_gust"],
                last_data["pressure"],
                last_data["rain_rate"],
                last_data["rain_total"],
                debug_state
            )
        else:
            html = "<html><body><h2>Noch keine Daten empfangen…</h2></body></html>"

        client.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
        client.send(html)
        client.close()

    time.sleep(0.3)
