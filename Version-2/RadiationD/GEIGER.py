from machine import Pin
import time
#
# Beispiel: Input @ GP17
GEIGER_PIN = 17
geiger = Pin(GEIGER_PIN, Pin.IN, Pin.PULL_UP)  # Pull-up wenn Spannungsteiler / opto genutzt
count = 0
last_pulse_us = 0
MIN_PULSE_SEPARATION_US = 150  # 150..300 µs Filter, an deine Messung anpassen

def geiger_irq(pin):
    global count, last_pulse_us
    t = time.ticks_us()
    if time.ticks_diff(t, last_pulse_us) > MIN_PULSE_SEPARATION_US:
        count += 1
        last_pulse_us = t

geiger.irq(trigger=Pin.IRQ_FALLING, handler=geiger_irq)

# Messzyklus (z. B. 60 s)
while True:
    count = 0
    t0 = time.ticks_ms()
    duration_s = 60
    end = t0 + duration_s*1000
    while time.ticks_ms() < end:
        time.sleep(0.2)  # IRQ zählt weiter
    cpm = int(count * (60.0 / duration_s))
    print("CPM:", cpm)
    # Umrechnung (einstellbar)
    FACTOR = 0.00812
    usvh = cpm * FACTOR
    print("Dose: {:.3f} µSv/h".format(usvh))
