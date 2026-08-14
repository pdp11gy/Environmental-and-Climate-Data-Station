# MOX Gas Sensor SGP30 test program
# No library required
#
from machine import I2C, Pin
import time
#
i2c = I2C(0, scl=Pin(1), sda=Pin(0))
# Initialisieren
i2c.writeto(0x58, bytes([0x20, 0x03]))
print("SGP30 init")
time.sleep(15)
#
while True:
    # Messung anfordern
    i2c.writeto(0x58, bytes([0x20, 0x08]))
    time.sleep_ms(50)
    data = i2c.readfrom(0x58, 6)
    print("RAW:", data)
    eco2 = (data[0] << 8) | data[1]
    tvoc = (data[3] << 8) | data[4]
    print("eCO2 =", eco2, "ppm")
    print("TVOC =", tvoc, "ppb")
    time.sleep(1)
    
