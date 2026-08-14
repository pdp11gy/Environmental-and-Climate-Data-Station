# Geiger_bmp280_OLED.py
# Geiger RadiationD-V1.1 (CAJOE) + bmp280 + SSD1306 OLED
#  https://pdp11gy.com/Climastation.html
#             www.pdp11gy.com   E-Mail: info@pdp11gy.com
#
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time
import dht
import bmp280
#
# --- OLED Setup (I2C1 auf GP14=SDA, GP15=SCL) ---
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)
#
# --- bmp280 Setup
i2c = I2C(0, scl=Pin(1), sda=Pin(0))
bmp = bmp280.BMP280(i2c, addr=0x76)
#
# --- Geigerzähler  Setup ---
# Geiger-Ausgang an GP17 (oder ändere auf GP16/GP17 wie Du brauchst)
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
#
# IRQ registrieren
geiger_pin.irq(trigger=Pin.IRQ_RISING, handler=geiger_irq)
# --- Umrechnungsfaktor CPM -> µSv/h (einstellbar) ---
# Default-Wert: 0.00812 (häufiger Referenzwert für einige Röhren; anpassen nach Röhrentyp)
CPM_TO_USV_PER_H = 0.00812
# Messperiode in Sekunden (60 => direkt CPM)
SAMPLE_SECONDS = 60
#
def display_results(pm_count_cpm, usvh, temp, pressure_hpa):
    oled.fill(0)
    oled.text("Geiger + BMP280", 0, 0)
    oled.text("CPM: {:d}".format(pm_count_cpm), 0, 14)
    oled.text("{:.3f} uSv/h".format(usvh), 0, 25)
    #
    oled.text(f"Temp: {temp:.1f} C", 0, 40)
    oled.text(f"Press: {pressure_hpa:} hPa", 0, 50)
    oled.show()
#
# --- Hauptschleife ---
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
    #
    # Auf OLED anzeigen
    display_results(cpm, usv_h, temp, pressure_hpa)
    #
    # Debugausgabe auf REPL
    print("CPM:", cpm, "uSv/h:", usv_h)
    # kurze Pause vor neuem Zyklus
    time.sleep(1)
