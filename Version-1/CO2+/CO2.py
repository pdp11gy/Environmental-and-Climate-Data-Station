# CO2 measurement, sensor MH-Z19C sensor.
#
from machine import UART, Pin
import time
#
uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
#uart1 = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
REQUEST_CO2 = b'\xFF\x01\x86\x00\x00\x00\x00\x00\x79'

time.sleep(5)  # Sensor-Aufwärmzeit

def checksum(data):
    # laut Datenblatt: 0xFF + 0x01 + ... + Byte7 -> 0xFF - Sum + 1
    return (0xFF - (sum(data[1:8]) % 256) + 1) & 0xFF

while True:
    uart0.write(REQUEST_CO2)
    time.sleep(0.1)

    if uart0.any():
        response = uart0.read(9)
        #print(response, " = CO2:")
        if response and len(response) == 9 and response[0] == 0xFF and response[1] == 0x86:
            # Prüfsumme vergleichen
            if response[8] == checksum(response):
                co2 = response[2] * 256 + response[3]
                temp = response[4] - 40
                status = response[5]
                
                # Statusbits interpretieren (je nach Firmware leicht unterschiedlich)
                if status == 0x00:
                    status_text = "OK"
                elif status == 0x10:
                    status_text = "Preheating"
                elif status == 0x20:
                    status_text = "Sensor error"
                else:
                    status_text = f"Unbekannt (0x{status:02X})"

                print(f"CO₂: {co2} ppm | Temp: {temp} °C | Status: {status_text}")
            else:
                print("❌ Prüfsummenfehler:", response)
        else:
            print("Fehlerhafte oder unvollständige Antwort:", response)
    else:
        print("Keine Antwort vom Sensor")

    time.sleep(2)
    