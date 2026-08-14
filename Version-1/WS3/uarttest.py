from machine import UART, Pin
uart = UART(0, baudrate=9600, tx=Pin(2), rx=Pin(1))
while True:
    if uart.any():
        data = uart.read()
        print(data)
