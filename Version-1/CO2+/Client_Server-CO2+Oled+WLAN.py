# CO2 measurement, sensor MH-Z19C sensor.
# Data display on OLED SSD1306 and data transmission
# via Wi-Fi, client (Pico) / server (Raspberry Pi)
# MicroPython SSD1306 OLED driver, I2C and SPI interfaces
# Projektreferenz:  PDP11GY-ENV-PICO-2025 and Hardware.pdf
#  https://pdp11gy.com/Climastation.html
#             www.pdp11gy.com   E-Mail: info@pdp11gy.com
#
from micropython import const
import framebuf
# register definitions
SET_CONTRAST = const(0x81)
SET_ENTIRE_ON = const(0xA4)
SET_NORM_INV = const(0xA6)
SET_DISP = const(0xAE)
SET_MEM_ADDR = const(0x20)
SET_COL_ADDR = const(0x21)
SET_PAGE_ADDR = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP = const(0xA0)
SET_MUX_RATIO = const(0xA8)
SET_COM_OUT_DIR = const(0xC0)
SET_DISP_OFFSET = const(0xD3)
SET_COM_PIN_CFG = const(0xDA)
SET_DISP_CLK_DIV = const(0xD5)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_CHARGE_PUMP = const(0x8D)

# Subclassing FrameBuffer provides support for graphics primitives
# http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
class SSD1306(framebuf.FrameBuffer):
    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00,  # off
            # address setting
            SET_MEM_ADDR,
            0x00,  # horizontal
            # resolution and layout
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01,  # column addr 127 mapped to SEG0
            SET_MUX_RATIO,
            self.height - 1,
            SET_COM_OUT_DIR | 0x08,  # scan from COM[N] to COM0
            SET_DISP_OFFSET,
            0x00,
            SET_COM_PIN_CFG,
            0x02 if self.width > 2 * self.height else 0x12,
            # timing and driving scheme
            SET_DISP_CLK_DIV,
            0x80,
            SET_PRECHARGE,
            0x22 if self.external_vcc else 0xF1,
            SET_VCOM_DESEL,
            0x30,  # 0.83*Vcc
            # display
            SET_CONTRAST,
            0xFF,  # maximum
            SET_ENTIRE_ON,  # output follows RAM contents
            SET_NORM_INV,  # not inverted
            # charge pump
            SET_CHARGE_PUMP,
            0x10 if self.external_vcc else 0x14,
            SET_DISP | 0x01,
        ):  # on
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)

    def poweron(self):
        self.write_cmd(SET_DISP | 0x01)

    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            # displays with width of 64 pixels are shifted by 32
            x0 += 32
            x1 += 32
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)


class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.write_list = [b"\x40", None]  # Co=0, D/C#=1
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.temp[0] = 0x80  # Co=1, D/C#=0
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf):
        self.write_list[1] = buf
        self.i2c.writevto(self.addr, self.write_list)


class SSD1306_SPI(SSD1306):
    def __init__(self, width, height, spi, dc, res, cs, external_vcc=False):
        self.rate = 10 * 1024 * 1024
        dc.init(dc.OUT, value=0)
        res.init(res.OUT, value=0)
        cs.init(cs.OUT, value=1)
        self.spi = spi
        self.dc = dc
        self.res = res
        self.cs = cs
        import time

        self.res(1)
        time.sleep_ms(1)
        self.res(0)
        time.sleep_ms(10)
        self.res(1)
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(buf)
        self.cs(1)
        
#------------------------------------------------------------------------------

from machine import UART, Pin, I2C
import network, socket, time
# -----------------------------
# CO2-SENSOR (MH-Z19C)
# -----------------------------
uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
REQUEST_CO2 = b'\xFF\x01\x86\x00\x00\x00\x00\x00\x79'
#
def co2_checksum(data):
    # Prüfsumme berechnen laut Datenblatt
    return (0xFF - (sum(data[1:8]) % 256) + 1) & 0xFF
def read_co2():
    uart0.write(REQUEST_CO2)
    time.sleep(0.1)
    if uart0.any():
        response = uart0.read(9)
        if response and len(response) == 9 and response[0] == 0xFF and response[1] == 0x86:
            if response[8] == co2_checksum(response):
                co2 = response[2] * 256 + response[3]
                temp = response[4] - 40
                status = response[5]
                return co2, temp, status
    return None, None, None

# --------- OLED Setup ---------
# I2C1 auf GP14=SDA, GP15=SCL
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
display = SSD1306_I2C(128, 64, i2c)
#
display.text("CO2 Sensor", 0, 0)
# -----------------------------
# WLAN-DATEN
# -----------------------------
SSID = "WLAN Name"
PASSWORD = "WLAN PASSWORD"
SERVER_IP = "IP von RASPberry PI"   # <- IP deines Raspberry Pi
SERVER_PORT = 5000                  # z. B. Flask oder kleiner Server
# -----------------------------
# WLAN-VERBINDUNG AUFBAUEN
# -----------------------------
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)
print("Verbinde mit WLAN...")
while not wlan.isconnected():
    time.sleep(0.5)
print("Verbunden mit:", wlan.ifconfig())

# IP anzeigen
display.fill(0)
display.text("WLAN verbunden", 0, 0)
display.text(wlan.ifconfig()[0], 0, 10)
display.show()
time.sleep(10)

# -----------------------------
# HAUPTSCHLEIFE
# -----------------------------
while True:
    uart0.write(REQUEST_CO2)
    time.sleep(0.1)
    response = uart0.read(9)

    if response and len(response) == 9 and response[0] == 0xFF and response[1] == 0x86:
        co2 = response[2] * 256 + response[3]
        print("CO2:", co2, "ppm")

        # OLED-Anzeige
        display.fill(0)
        display.text("CO2 Sensor", 0, 0)
        display.text("Wert:", 0, 20)
        display.text(str(co2) + " ppm", 0, 35)
        display.show()

        # An Raspi senden
        try:
            addr = socket.getaddrinfo(SERVER_IP, SERVER_PORT)[0][-1]
            s = socket.socket()
            s.connect(addr)
            msg = f"CO2={co2}\n"
            s.send(msg.encode())
            s.close()
        except Exception as e:
            print("Sendefehler:", e)
    else:
        print("Fehlerhafte Daten:", response)

    time.sleep(5)
"""
# Datei: server.py  = SERVER
import socket

HOST = "0.0.0.0"
PORT = 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("Warte auf Daten von Pico...")
    while True:
        conn, addr = s.accept()
        with conn:
            data = conn.recv(1024)
            if data:
                print(f"{addr}: {data.decode().strip()}")

#@PI, enter:
#python3 server.py
"""