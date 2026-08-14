# Client/Server version including Raspberry Pi Zero 2W
# Test program for LTR390UV (UV) and SGP30 (gas) sensors
# UV radiation in milliwatts per square centimeter (mW/cm²)
# eCO2 measurement: ppm; TVOC measurement: ppb
# No sensor library required
# Wiring: see image UV+GAS-Testaufbau.jpg
# Display output via SSD1306 OLED
#
# Requires corresponding (additional) entry in server.py
#
#   {% elif val.sensor == "UVuGas" %}
#   <div class="value">UV:    {{val.uv_raw}}  mWqcm</div>
#   <div class="value">eCO2:  {{val.eco2}}  ppm</div>
#   <div class="value">TVOC:  {{val.tvoc}}  ppb</div>
#
# https://pdp11gy.com/Wetterstation.html, info@pdp11gy.com
#
from micropython import const
import framebuf  
from machine import I2C, Pin
from ssd1306 import SSD1306_I2C
import network
import urequests
import machine
import time
#
# LTR390 UV Sensor an I2C0 (SDA=GP0, SCL=GP1)
LTR390 = 0x53
i2c0 = I2C(0, scl=Pin(1), sda=Pin(0))
# SGP30 Lufqualität an I2C1 ((SDA=GP0, SCL=GP1)
SGP30 = 0x58
i2c1 = I2C(0, scl=Pin(1), sda=Pin(0))
# OLED-Display an I2C1 (SDA=GP14, SCL=GP15)
i2c2 = I2C(1, scl=Pin(15), sda=Pin(14))
oled = SSD1306_I2C(128, 64, i2c2)
#
led = machine.Pin("LED", machine.Pin.OUT)
#
#SERVER = "http://192.168.178.80:5000/data"  # My Station 1
SERVER = "http://192.168.178.72:5000/data"   # My Station 2
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
def send_uvgas(uv_raw,eco2,tvoc):
    try:        
        data = {
            "sensor": "UVuGas",
            "uv_raw": round(uv_raw, 1),
            "eco2":   round(eco2, 1),
            "tvoc":   round(tvoc, 1)
        }
        r = urequests.post(SERVER, json=data)
        r.close()
    except Exception as e:
        print("Sendefehler:", e)
#
# LTR390 Sensor einschalten:
i2c0.writeto_mem(LTR390, 0x00, bytes([0x0A]))
# SGP30 Sensor einschalten:
oled.fill(0)
oled.text("LTR390 und SGP30",0,10)
oled.text("INIT,wait 15 sec",0,30)
oled.show()
i2c1.writeto(0x58, bytes([0x20, 0x03]))                # INIT
time.sleep(15)
i2c0.writeto_mem(LTR390, 0x05, bytes([0x03]))          # aktivieren Gainx3
#
# -------------------------------
# Hauptloop
# -------------------------------
led.value(0)
while True:
    i2c1.writeto(0x58, bytes([0x20, 0x08]))            # SGP30 Messung anfordern
    time.sleep_ms(50)
    oled.fill(0) 
    oled.text("LTR390 UV Sensor",0,3)
    uv0 = i2c0.readfrom_mem(LTR390, 0x10, 1)[0]
    uv1 = i2c0.readfrom_mem(LTR390, 0x11, 1)[0]
    uv2 = i2c0.readfrom_mem(LTR390, 0x12, 1)[0]
    uv_raw = uv0 | (uv1 << 8) | (uv2 << 16)
    oled.text("LTR390 UV Sensor",0,3)
    oled.text("UV:  {} mW/qcm".format(uv_raw), 0, 16)
    oled.text("------------------",0,24)
    oled.text("SGP30 GAS Sensor",0,34)
    data = i2c1.readfrom(0x58, 6)
    eco2 = (data[0] << 8) | data[1]
    tvoc = (data[3] << 8) | data[4]
    oled.text("eCOS:  {} ppm".format(eco2), 0, 44)
    oled.text("TVOC:  {} ppb".format(tvoc), 0, 54)
    oled.show()
    #print("UV= ", uv_raw, "mW/qcm")
    #print("eCO2 =", eco2, "ppm")
    #print("TVOC =", tvoc, "ppb")
    #print("------------------------")
    #
    #---------------------------!
    #print(uv_raw,eco2,tvoc)
    send_uvgas(uv_raw,eco2,tvoc)
    #
    led.toggle()   # Zustand umschalten
    time.sleep(0.2)
    led.toggle()   # Zustand umschalten
    time.sleep(0.2)
    led.toggle()   # Zustand umschalten
    time.sleep(0.2)
    led.toggle()   # Zustand umschalten
     #---------------------------!
    time.sleep(5)
#
