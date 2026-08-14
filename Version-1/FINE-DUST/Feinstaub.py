from machine import UART, Pin
import time

uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

def read_sds011():
    if uart0.any() >= 10:  # SDS011 sendet 10-Byte-Pakete
        data = uart0.read(10)
        if data and data[0] == 0xAA and data[1] == 0xC0 and data[9] == 0xAB:
            pm25 = (data[3]*256 + data[2])/10.0
            pm10 = (data[5]*256 + data[4])/10.0
            return pm25, pm10
    return None, None

while True:
    pm25, pm10 = read_sds011()
    if pm25 is not None:
        print("PM2.5: {:.1f} µg/m³  PM10: {:.1f} µg/m³".format(pm25, pm10))
    time.sleep(2)
