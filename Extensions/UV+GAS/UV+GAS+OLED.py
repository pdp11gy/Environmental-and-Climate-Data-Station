# UV and Gas Sensor LTR390UV+SGP30 Test Program
# UV radiation in milliwatts per square centimeter (mW/cm²)
# eCO2 measurement: ppm; TVOC measurement: ppb
# No sensor library required
# Wiring: see image UV+GAS-Testaufbau.jpg
# Display output with SSD1306 OLED support
#  https://pdp11gy.com/Climastation.html
#             www.pdp11gy.com   E-Mail: info@pdp11gy.com
#
from micropython import const
import framebuf  
from machine import I2C, Pin
from ssd1306 import SSD1306_I2C
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
# LTR390 Sensor einschalten:
i2c0.writeto_mem(LTR390, 0x00, bytes([0x0A]))
# SGP30 Sensor einschalten:
oled.fill(0)
oled.text("LTR390 und SGP30",0,10)
oled.text("INIT,wait 15 sec",0,30)
oled.show()
i2c1.writeto(0x58, bytes([0x20, 0x03]))
#print("LTR390 und SGP30 init ..... wait 15 Sekunden")
time.sleep(15)
#
# Gain:
#i2c.writeto_mem(LTR390, 0x05, bytes([0x01]))
i2c0.writeto_mem(LTR390, 0x05, bytes([0x03]))           # aktivieren Gainx3
#i2c.writeto_mem(LTR390, 0x05, bytes([0x04]))
#
ctrl = i2c0.readfrom_mem(LTR390, 0x00, 1)[0]
print("controll register Hex:",(hex(ctrl)))
#
while True:
    i2c1.writeto(0x58, bytes([0x20, 0x08]))            # SGP30 Messung anfordern
    time.sleep_ms(50)
    oled.fill(0) 
    oled.text("LTR390 UV Sensor",0,3)
    uv0 = i2c0.readfrom_mem(LTR390, 0x10, 1)[0]
    uv1 = i2c0.readfrom_mem(LTR390, 0x11, 1)[0]
    uv2 = i2c0.readfrom_mem(LTR390, 0x12, 1)[0]
    uv_raw = uv0 | (uv1 << 8) | (uv2 << 16)
    #print("raw-daten:",uv_raw)
    oled.text("LTR390 UV Sensor",0,3)
    oled.text("UV:  {} mW/qcm".format(uv_raw), 0, 16)
    oled.text("------------------",0,24)
    oled.text("SGP30 GAS Sensor",0,34)
    data = i2c1.readfrom(0x58, 6)
    eco2 = (data[0] << 8) | data[1]
    tvoc = (data[3] << 8) | data[4]
    oled.text("eCOS:  {} ppm".format(eco2), 0, 44)
    oled.text("TVOC:  {} ppb".format(tvoc), 0, 54)
    #print("eCO2 =", eco2, "ppm")
    #print("TVOC =", tvoc, "ppb")    
    oled.show()
    time.sleep(1)
#
