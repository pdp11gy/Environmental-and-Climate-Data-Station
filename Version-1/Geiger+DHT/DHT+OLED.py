from machine import Pin, I2C
import time
import dht
from ssd1306 import SSD1306_I2C   # Stelle sicher, dass ssd1306.py im Pico liegt

# DHT22 Sensor an GP16 (Pin 21)
sensor = dht.DHT22(Pin(16))

# OLED-Display an I2C1 (SDA=GP14, SCL=GP15)
i2c = I2C(1, scl=Pin(15), sda=Pin(14))
oled = SSD1306_I2C(128, 64, i2c)

while True:
    try:
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()

        # OLED leeren
        oled.fill(0)

        # Werte anzeigen
        oled.text("DHT22 Sensor", 0, 0)
        oled.text("Temp: {:.1f} C".format(temp), 0, 20)
        oled.text("Feuchte: {:.1f}%".format(hum), 0, 40)

        # Anzeige aktualisieren
        oled.show()

        print("Temperatur:", temp, "°C", "Feuchte:", hum, "%")
        time.sleep(2)

    except OSError as e:
        print("Sensorfehler:", e)
        oled.fill(0)
        oled.text("Fehler beim", 0, 20)
        oled.text("lesen des Sensors", 0, 35)
        oled.show()
        time.sleep(2)
