# Radio-UV-Luft-Client_V4_3.py
#           ****** Radiation-Station *******
# Geiger RadiationD-V1.1+LTR390+BMP280+SSD1306+OLED
#                   WLAN
# Hardware Version 2, re. Hardware.pdf, chapter 3
# Server Versions: server_V4_3.py / server_V2_3.py
#  https://pdp11gy.com/Climastation.html
#             www.pdp11gy.com   E-Mail: info@pdp11gy.com
# -------------------------------------------------------------
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import network
import urequests
import time
import machine
import bmp280
#
# LTR390 UV Sensor an I2C0 (SDA=GP0, SCL=GP1)
LTR390 = 0x53
i2c0 = I2C(0, scl=Pin(1), sda=Pin(0))
#
# --- OLED Setup (I2C1 auf GP14=SDA, GP15=SCL) ---
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)
#
# --- bmp280 Setup
i2c = I2C(0, scl=Pin(1), sda=Pin(0))
bmp = bmp280.BMP280(i2c, addr=0x76)
#
# *************************  Geigerzähler  Setup *******************************
# Geiger-Ausgang an GP17 
# Achtung: wenn Geiger-Ausgang 5V ist -> Levelshifter verwenden!!!
geiger_pin_num = 17
geiger_pin = Pin(geiger_pin_num, Pin.IN, Pin.PULL_DOWN)
# Zählvariablen
count = 0
last_pulse_us = 0
# Entprell/Abstand in Mikrosekunden (z.B. 200 µs)
MIN_PULSE_SEPARATION_US = 200
#
def geiger_irq(pin):
    global count, last_pulse_us
    t = time.ticks_us()
    # Ignoriere sehr schnelle Folgepulse (Hardware-Rauschen)
    if time.ticks_diff(t, last_pulse_us) > MIN_PULSE_SEPARATION_US:
        count += 1
        last_pulse_us = t
# IRQ registrieren
geiger_pin.irq(trigger=Pin.IRQ_RISING, handler=geiger_irq)
# --- Umrechnungsfaktor CPM -> µSv/h (einstellbar) ---
# Default-Wert: 0.00812 (häufiger Referenzwert für einige Röhren; anpassen nach Röhrentyp)
CPM_TO_USV_PER_H = 0.00812
# Messperiode in Sekunden (60 => direkt CPM)
SAMPLE_SECONDS = 60
# ****************************************************************************
#
# V4_2: def display_results(pm_count_cpm, usvh, temp, pressure_hpa):
def display_results(pm_count_cpm, usvh, uv_raw, temp, pressure_hpa):
    oled.fill(0)
    oled.text("Strahlenstation", 0, 1)
    oled.text("CPM: {:d}".format(pm_count_cpm), 0, 14)
    oled.text("{:.3f} uSv/h".format(usvh), 0, 23)
    #oled.text("UV:  {}mW/qcm".format(uv_raw), 0, 33)
    oled.text("UV-Raw: {}".format(uv_raw), 0, 33)
    oled.text(f"Temp: {temp:.1f} C", 0, 45)
    oled.text(f"Press: {pressure_hpa:} hPa", 0, 57)
    #
    oled.show()
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
# V4_2: def send_geiger(pm_count_cpm, usvh, temperature, pressure):
def send_geiger(pm_count_cpm, usvh, uv_raw, temperature, pressure):
    try:        
        data = {
            "station": "station1u2",
            "sensor": "geiger",
            "cpm": round(pm_count_cpm, 1),
            "usvh": round(usvh, 3),
            "uv_raw": round(uv_raw, 1),
            "temperature": round(temperature, 1),
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
# LTR390 Sensor einschalten
i2c0.writeto_mem(LTR390, 0x00, bytes([0x0A]))
#status = i2c0.readfrom_mem(LTR390, 0x07, 1)[0]
#print("status register: ",bin(status))
# Gain:
#i2c.writeto_mem(LTR390, 0x05, bytes([0x01]))           # Gainx1
i2c0.writeto_mem(LTR390, 0x05, bytes([0x03]))           # >aktivieren Gainx3
#i2c.writeto_mem(LTR390, 0x05, bytes([0x04]))           # Gainx4
#
#---------------------------------------
# Hauptschleife 
#---------------------------------------
while True:
    count = 0                            # zurücksetzen und 60 s zählen
    t0 = time.ticks_ms()
    wait_until = t0 + SAMPLE_SECONDS*1000
    #
    # während der Wartezeit kann IRQ weiter zählen
    while time.ticks_ms() < wait_until:
        time.sleep(0.2)                  # kleine Sleep, IRQ läuft weiterhin
    cpm = int(count)                     # Counts Per Minute (über SAMPLE_SECONDS==60 direkt CPM)
    # Falls SAMPLE_SECONDS != 60, hochrechnen:
    # cpm = int(count * (60.0 / SAMPLE_SECONDS))
    #
    # µSv/h berechnen
    usv_h = cpm * CPM_TO_USV_PER_H
    #
    # bmp280 auslesen (nicht-blockierend, mit Fehlerbehandlung)
    temp = bmp.temperature        # °C
    pressure = bmp.pressure       # Pa → hPa
    pressure_hpa = int(pressure / 100)
    # LTR390 auslesen
    uv0 = i2c0.readfrom_mem(LTR390, 0x10, 1)[0]
    uv1 = i2c0.readfrom_mem(LTR390, 0x11, 1)[0]
    uv2 = i2c0.readfrom_mem(LTR390, 0x12, 1)[0]
    uv_raw = uv0 | (uv1 << 8) | (uv2 << 16)
    # Auf OLED anzeigen
    display_results(cpm, usv_h, uv_raw, temp, pressure_hpa)
    # V4_2: display_results(cpm, usv_h, temp, pressure_hpa)
    # Debugausgabe auf REPL
    # print("CPM:", cpm, "uSv/h:", usv_h, "   UV-daten:",uv_raw)
    #
    #---------------------------------------------------+
    send_geiger(cpm, usv_h, uv_raw, temp, pressure_hpa)
    # V4_2: send_geiger(cpm, usv_h, temp, pressure_hpa)
    led.toggle()   # Zustand umschalten
    time.sleep(0.2)
    led.toggle()   # Zustand umschalten
    time.sleep(0.2)
    led.toggle()   # Zustand umschalten
    time.sleep(0.2)
    led.toggle()   # Zustand umschalten
    #---------------------------------------------------+
    # kurze Pause vor neuem Zyklus
    time.sleep(1)
