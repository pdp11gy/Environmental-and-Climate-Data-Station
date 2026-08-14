# UV + ALS Sensor LTR390UV Test Program
# Without ALS mode. No library required
# Version with OLED support
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
# OLED-Display an I2C1 (SDA=GP14, SCL=GP15)
i2c2 = I2C(1, scl=Pin(15), sda=Pin(14))
oled = SSD1306_I2C(128, 64, i2c2)
#
#partid = i2c0.readfrom_mem(LTR390, 0x06, 1)
print("Part ID:", hex(partid[0]))
#
# LTR390 Sensor einschalten
i2c0.writeto_mem(LTR390, 0x00, bytes([0x0A]))
#
status = i2c0.readfrom_mem(LTR390, 0x07, 1)[0]
print("status register: ",bin(status))
#
# Gain:
#i2c.writeto_mem(LTR390, 0x05, bytes([0x01]))
i2c0.writeto_mem(LTR390, 0x05, bytes([0x03]))           # aktivieren Gainx3
#i2c.writeto_mem(LTR390, 0x05, bytes([0x04]))
#
ctrl = i2c0.readfrom_mem(LTR390, 0x00, 1)[0]
print("controll register Hex:",(hex(ctrl)))
#
oled.fill(0) 
while True:
    oled.fill(0) 
    oled.text("LTR390 UV Sensor",0,3)
    uv0 = i2c0.readfrom_mem(LTR390, 0x10, 1)[0]
    uv1 = i2c0.readfrom_mem(LTR390, 0x11, 1)[0]
    uv2 = i2c0.readfrom_mem(LTR390, 0x12, 1)[0]
    uv_raw = uv0 | (uv1 << 8) | (uv2 << 16)
    oled.text("UV:  {}mW/qcm".format(uv_raw), 0, 16)
    oled.text("------------------",0,24)
    print("raw-daten:",uv_raw)
    oled.show()
    time.sleep(1)
#
