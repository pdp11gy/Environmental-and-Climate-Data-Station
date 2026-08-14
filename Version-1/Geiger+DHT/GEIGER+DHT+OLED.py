# GEIGER+DHT11+OLED.py
# Geiger RadiationD-V1.1 (CAJOE) + DHT11 + SSD1306 OLED
#
from machine import Pin, I2C
import time
import dht
from ssd1306 import SSD1306_I2C
#
# --- OLED Setup (I2C1 auf GP14=SDA, GP15=SCL) ---
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)
#
# --- DHT11 Setup (z. B. GP16) ---
dht_pin = Pin(16, Pin.IN, Pin.PULL_UP)
dht_sensor = dht.DHT22(dht_pin)  # oder DHT22 falls Du den hast
#
# --- Geiger Setup ---
# Geiger-Ausgang an GP17 (oder ändere auf GP16/GP17 wie Du brauchst)
# Achtung: wenn Geiger-Ausgang 5V ist -> Levelshifter verwenden!!!
geiger_pin_num = 17
geiger_pin = Pin(geiger_pin_num, Pin.IN, Pin.PULL_DOWN)
#
# Zählvariablen
count = 0
last_pulse_us = 0
#
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
#
# IRQ registrieren
geiger_pin.irq(trigger=Pin.IRQ_RISING, handler=geiger_irq)
#
# --- Umrechnungsfaktor CPM -> µSv/h (einstellbar) ---
# Default-Wert: 0.00812 (häufiger Referenzwert für einige Röhren; anpassen nach Röhrentyp)
CPM_TO_USV_PER_H = 0.00812
#
# Messperiode in Sekunden (60 => direkt CPM)
SAMPLE_SECONDS = 60
#
def display_results(pm_count_cpm, usvh, temp=None, hum=None):
    oled.fill(0)
    oled.text("Geiger + DHT", 0, 0)
    oled.text("CPM: {:d}".format(pm_count_cpm), 0, 16)
    oled.text("{:.3f} uSv/h".format(usvh), 0, 30)
    if temp is not None and hum is not None:
        oled.text("T:{:.1f}C H:{:.0f}%".format(temp, hum), 0, 46)
    oled.show()
#
# --- Hauptschleife ---
while True:
    # zurücksetzen und 60 s zählen
    count = 0
    t0 = time.ticks_ms()
    wait_until = t0 + SAMPLE_SECONDS*1000
    # während der Wartezeit kann IRQ weiter zählen
    while time.ticks_ms() < wait_until:
        time.sleep(0.2)  # kleine Sleep, IRQ läuft weiterhin
    cpm = int(count)  # Counts Per Minute (über SAMPLE_SECONDS==60 direkt CPM)
    # Falls SAMPLE_SECONDS != 60, hochrechnen:
    # cpm = int(count * (60.0 / SAMPLE_SECONDS))
    #
    # µSv/h berechnen
    usv_h = cpm * CPM_TO_USV_PER_H
    #
    # DHT auslesen (nicht-blockierend, mit Fehlerbehandlung)
    try:
        dht_sensor.measure()
        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()
    except Exception as e:
        temperature = None
        humidity = None

    # Auf OLED anzeigen
    display_results(cpm, usv_h, temperature, humidity)

    # Debugausgabe auf REPL
    print("CPM:", cpm, "uSv/h:", usv_h, "T:", temperature, "H:", humidity)
    # kurze Pause vor neuem Zyklus
    time.sleep(1)
