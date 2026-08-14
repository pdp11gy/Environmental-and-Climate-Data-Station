# -------------------------------------------------------------
#  CO2+OLED+WLAN_V1.py  based on Raspberry PI PICO w
#  Kohlendioxid-CO2 MH-Z19C + OLED + WLAN + Webserver 
#  Version 1 — stabiler UART-Parser, stabile Sockets
#  Debug Mode: on/off via Browser.
#  Typisches Daten-Format b'\xff\x86\x05!?\x00\x00\x00\x15'
# Projektreferenz:  PDP11GY-ENV-PICO-2025 and Hardware.pdf
#  https://pdp11gy.com/Climastation.html
#             www.pdp11gy.com   E-Mail: info@pdp11gy.com
# -------------------------------------------------------------
import network
import socket
import time
from machine import Pin, I2C, UART
from ssd1306 import SSD1306_I2C
#
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
# MH-Z19C Setup
# ---------------------------------------------------------
uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
REQUEST = b'\xFF\x01\x86\x00\x00\x00\x00\x00\x79'
#
def read_co2():
    global last_raw, last_ok

    uart0.write(REQUEST)
    time.sleep_ms(120)

    if uart0.any() < 9:
        last_ok = False
        return None, None, False

    resp = uart0.read(9)
    last_raw = resp

    if not resp or len(resp) != 9:
        last_ok = False
        return None, None, False

    if resp[0] != 0xFF or resp[1] != 0x86:
        last_ok = False
        return None, None, False

    # Werte extrahieren
    co2  = resp[2] * 256 + resp[3]
    temp = resp[4] - 40

    if DEBUG:
        print("RAW:", resp)
        print("CO2:", co2, "Temp:", temp)
        print("-----------------------------------")
    else:
        print(".", end="")
    last_ok = True
    return co2, temp, True

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
        ip = wlan.ifconfig()[0]
        print("Verbunden:", ip)
        return ip
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

# ---------------------------------------------------------
# Hauptloop
# ---------------------------------------------------------
while True:
    co2, temp, ok = read_co2()
    # OLED
    oled.fill(0)
    oled.text("CO2 mit MH-Z19C", 0, 0)

    if ok:
        oled.text("CO2 : {} ppm".format(co2), 0, 16)
        oled.text("Temp: {} C".format(temp), 0, 32)
    else:
        oled.text("Warte auf Daten...", 0, 16)

    #oled.text("IP:{}".format(ip), 0, 48)
    oled.text("{}".format(ip), 0, 48)   
    oled.show()

    # HTTP Handling
    try:
        cl, addr = server.accept()
        cl_file = cl.makefile("rwb", 0)

        request = ""
        while True:
            line = cl_file.readline()
            if not line or line == b"\r\n":
                break
            request += line.decode()

        # Debug per URL
        if "/debug?on=true" in request:
            DEBUG = True
        if "/debug?on=false" in request:
            DEBUG = False

        # HTML erzeugen
        html = """\
<html>
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="5">
<title>CO2 Sensor V4.1</title>
</head>
<body>
<h2>Kohlendioxyd=CO2 und Temperatur MH-Z19C</h2>
<p><b>CO2:</b> {} ppm</p>
<p><b>Temp:</b> {} °C</p>
<hr>
<p><b>Debug-Modus:</b> {}</p>
<p><a href="/debug?on=true">Debug EIN</a> |
<a href="/debug?on=false">Debug AUS</a></p>
""".format(co2 if ok else 0,
           temp if ok else 0,
           "Aktiv" if DEBUG else "Inaktiv")

        if DEBUG:
            html += "<hr><h3>Debug-Infos:</h3>"
            html += "<p>Raw: {}</p>".format(last_raw)
            html += "<p>Paket OK: {}</p>".format(last_ok)

        html += "</body></html>"

        cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
        cl.send(html)
        cl.close()

    except Exception as e:
        print("HTTP Fehler:", e)

    time.sleep(0.1)
