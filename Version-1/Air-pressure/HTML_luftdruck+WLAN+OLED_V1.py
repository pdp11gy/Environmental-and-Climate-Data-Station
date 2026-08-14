# -------------------------------------------------------
# BMP280 + OLED + WLAN
# Data display on OLED SSD1306 and data transmission
# via Wi-Fi, I2C1: SDA = GP14, SCL = GP15
# -------------------------------------------------------
import time
import network
import socket
from machine import Pin, I2C
import bmp280
from ssd1306 import SSD1306_I2C
# -------------------------------------------------------
# SICHERES NETZ + SOCKET RESET
# -------------------------------------------------------

def safe_cleanup():
    # WLAN deaktivieren
    try:
        wlan = network.WLAN(network.STA_IF)
        if wlan.active():
            wlan.active(False)
            time.sleep(0.2)
    except:
        pass

    # Offene Sockets schließen
    try:
        s = socket.socket()
        s.close()
    except:
        pass

    # I2C freigeben
    try:
        I2C(0).deinit()
    except:
        pass
    try:
        I2C(1).deinit()
    except:
        pass

    time.sleep(0.5)

safe_cleanup()

# -------------------------------------------------------
# I2C INITIALISIEREN
# -------------------------------------------------------
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)

# Sensor + Display
bmp = bmp280.BMP280(i2c, addr=0x76)
oled = SSD1306_I2C(128, 64, i2c)

# WLAN Daten
WIFI_SSID  = "WLAN-Name"
WIFI_PASS  = "WLAN-Password"

# -------------------------------------------------------
# WLAN CONNECT
# -------------------------------------------------------
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)

    # Defensiv: immer sauber neu starten
    wlan.active(False)
    time.sleep(0.2)
    wlan.active(True)

    wlan.connect(WIFI_SSID, WIFI_PASS)
    print("Verbinde mit WLAN...", end="")

    t0 = time.time()
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.3)

        # Timeout nach 10 Sekunden
        if time.time() - t0 > 10:
            print("\nWLAN Timeout! Neustart...")
            time.sleep(2)
            machine.reset()

    print("\nVerbunden!")
    print("IP:", wlan.ifconfig()[0])
    return wlan.ifconfig()[0]

ip = connect_wifi()

# -------------------------------------------------------
# BMP280 AUSLESEN
# -------------------------------------------------------
def get_bmp():
    temp = bmp.temperature
    pressure_hpa = int(bmp.pressure / 100)
    return temp, pressure_hpa

# -------------------------------------------------------
# WEBSERVER START
# -------------------------------------------------------
def start_server():
    # Socket neu erstellen
    s = socket.socket()
    # Port sofort wiederverwendbar, verhindert EADDRINUSE
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    addr = ('0.0.0.0', 80)
    s.bind(addr)
    s.listen(1)
    print("Webserver läuft: http://{}".format(ip))
    return s

server = start_server()

# -------------------------------------------------------
# HAUPTSCHLEIFE
# -------------------------------------------------------
while True:
    try:
        client, addr = server.accept()
        client.settimeout(3)  # damit blockiert er nicht ewig
        print("Verbindung von:", addr)

        request = client.recv(1024)

        # Sensor lesen
        temp, press = get_bmp()

        print("Temp:", temp, "°C  Druck:", press, "hPa")
        print("--------------------------")
        # OLED
        oled.fill(0)
        oled.text("BMP280 Sensor", 0, 0)
        oled.text("Temp: {:.1f} C".format(temp), 0, 20)
        oled.text("Press: {} hPa".format(press), 0, 40)
        oled.show()

        # HTML Ausgabe
        html = """<!DOCTYPE html>
<html>
<head>
<meta http-equiv="refresh" content="5">
<title>BMP280</title></head>
<body>
<h2>BMP280 Wetterstation</h2>
<p><b>Temperatur:</b> {:.2f} C</p>
<p><b>Luftdruck:</b> {} hPa</p>
</body>
</html>""".format(temp, press)

        client.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
        client.send(html)

    except Exception as e:
        print("Fehler:", e)

    finally:
        try:
            client.close()
        except:
            pass
