import dht
from machine import Pin
import time

sensor = dht.DHT22(Pin(16))  # oder DHT11

while True:
    try:
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()
        print("Temp: {:.1f}°C  Hum: {:.1f}%".format(temp, hum))
    except OSError:
        print("Fehler beim Auslesen")
    time.sleep(2)
