from machine import I2C, Pin
import bme680
# MBE680,SDA --> PICO GPIO0,PIN 1 
# MBE680,SCL --> PICO GPIO1,PIN 2
i2c = I2C(0, scl=Pin(1), sda=Pin(0))
sensor = bme680.BME680_I2C(i2c, address=0x77)
#
while True:
    print("Temp:", sensor.temperature)
    print("Humidity:", sensor.humidity)
    print("Pressure:", sensor.pressure)
    print("Gas:", sensor.gas)
    print("-------------------")