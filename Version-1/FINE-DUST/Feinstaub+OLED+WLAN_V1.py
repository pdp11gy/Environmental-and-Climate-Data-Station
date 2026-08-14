# -------------------------------------------------------------
#  Feinstaub+OLED+WLAN_V1.py  based on Raspberry PI PICO w
#  Feinstaub Sensor SDS011 + OLED + WLAN + Webserver 
#  Version 1 — stabiler UART-Parser, stabile Sockets und
#  Debug Mode: Ein/Aus via Browser.
#  Typisches Daten-Format b'\xaa\xc0\x10\x00$\x00\x170{\xab'
#  Projekt Referenz PDP11GY-ENV-PICO-2025
#  https://www.pdp11gy.com/dokumente/WetterstationPLUS.zip
# -------------------------------------------------------------
import network
import socket
import time
from machine import Pin, I2C, UART
from ssd1306 import SSD1306_I2C
# ---------------------------------------------------------
# WLAN Daten
# ---------------------------------------------------------
SSID = "Dein WLAN-Name"
PW   = "Dein WLAN-Password"
# ---------------------------------------------------------
# Globale Flags
# ---------------------------------------------------------
DEBUG = False
last_raw = None
last_ok = False

# ---------------------------------------------------------
# SDS011 Setup
# ---------------------------------------------------------
uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

def read_sds011():
    global last_raw, last_ok

    while uart0.any():
        b = uart0.read(1)
        if not b:
            return None, None, False
            #
        if b[0] == 0xAA:
            frame = b + uart0.read(9)
            last_raw = frame

            if len(frame) == 10 and frame[1] == 0xC0 and frame[9] == 0xAB:
                pm25 = (frame[3]*256 + frame[2]) / 10.0
                pm10 = (frame[5]*256 + frame[4]) / 10.0
                if DEBUG:
                    print("-----------------------------------")
                    print(last_raw)
                    print("pm25:",pm25,"   pm10:",pm10)
                else:
                     print(".", end="")
                last_ok = True
                return pm25, pm10, True
                #
            last_ok = False
            #
    return None, None, False
# ---------------------------------------------------------
# OLED Setup
# ---------------------------------------------------------
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)
# ---------------------------------------------------------
# WLAN verbinden
# ---------------------------------------------------------
def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PW)

    print("Verbinde mit WLAN...")
    for _ in range(30):
        if wlan.isconnected():
            break
        time.sleep(1)

    if wlan.isconnected():
        print("Verbunden:", wlan.ifconfig()[0])
        return wlan.ifconfig()[0]
    else:
        print("Fehler: WLAN Timeout")
        return None

ip = wifi_connect()

# ---------------------------------------------------------
# Webserver
# ---------------------------------------------------------
def start_webserver():
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print("Webserver läuft → http://{}".format(ip))
    return s

server = start_webserver()
#
# ---------------------------------------------------------
# Hauptloop
# ---------------------------------------------------------
while True:
    pm25, pm10, ok = read_sds011()

    # OLED aktualisieren
    oled.fill(0)
    if ok:
        oled.text("SDS011 Feinstaub", 0, 0)
        oled.text("PM2.5: {:.1f}".format(pm25), 0, 16)
        oled.text("PM10 : {:.1f}".format(pm10), 0, 32)
    else:
        oled.text("Warte auf Daten...", 0, 16)
    oled.text("IP: {}".format(ip), 0, 48)
    oled.show()

    # HTTP Anfrage
    try:
        cl, addr = server.accept()
        cl_file = cl.makefile("rwb", 0)

        request = ""
        while True:
            line = cl_file.readline()
            if not line or line == b"\r\n":
                break
            request += line.decode()
        # -----------------------------------------
        # Debug per URL schalten
        # -----------------------------------------
        if "/debug?on=true" in request:
            DEBUG = True

        if "/debug?on=false" in request:
            DEBUG = False
        debug_state = "Aktiv" if DEBUG else "Inaktiv"
        # -----------------------------------------
        # HTML Seite
        # -----------------------------------------
        html = """\
<html>
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="5">
<title>Feinstaub FS1.1</title>
</head>
<body>
<h2>SDS011 Feinstaubmessung</h2>
<p><b>PM2.5:</b> {:.1f} µg/m³</p>
<p><b>PM10 :</b> {:.1f} µg/m³</p>
<hr>
<p><b>Debug-Modus:</b> {}</p>
<p><a href="/debug?on=true">Debug EIN</a> | 
<a href="/debug?on=false">Debug AUS</a></p>
""".format(pm25 if ok else 0, pm10 if ok else 0, "Aktiv" if DEBUG else "Inaktiv")

        # Debug-Infos ausgeben
        if DEBUG:
            html += "<hr><h3>Debug-Infos:</h3>"
            html += "<p>Raw: {}</p>".format(last_raw)
            html += "<p>Paket OK: {}</p>".format(last_ok)

        html += "</body></html>"

        # Antwort senden
        cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
        cl.send(html)
        cl.close()

    except Exception as e:
        print("HTTP Fehler:", e)

    time.sleep(0.1)
