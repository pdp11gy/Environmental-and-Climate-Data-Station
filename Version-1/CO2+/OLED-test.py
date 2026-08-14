# Test/Demo Program for OLED Display SSD1306
# Library ssd1306.py required
from micropython import const
import framebuf       
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time

# Define the display and size (128x32)
# OLED-Display an I2C1 (SDA=GP14, SCL=GP15)
i2c = I2C(1, scl=Pin(15), sda=Pin(14))
oled = SSD1306_I2C(128, 64, i2c)

# Clear the display first
oled.fill(0) 

# Write a line of text to the display
oled.text("OLED DisplayTest",0,3)
oled.text("------------------",0,16)
oled.text("  Wetterstation",0,25)
oled.text("------------------",0,35)
oled.text(" WWW.PDP11GY.com",0,45)
oled.text("info@pdp11gy.com",0,57)

# Update the display
oled.show()

