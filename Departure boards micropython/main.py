"""
Author: Adam Knowles
Version: 0.1
Name: main.py
Description: Mini Pico W OLED departure boards for model railway

GitHub Repository: https://github.com/Pharkie/picow-railway-departure
Based on work by Stewart Watkiss - PenguinTutor
License: GNU General Public License (GPL)
"""
from machine import Pin, I2C
import network
import utime
from ssd1306 import SSD1306_I2C
from wifi_creds import WIFI_SSID, WIFI_PASSWORD

TEXT_X = 0
TEXT_Y = 0
TEXT_Y_SPACE = 12

# Set as global
oled = None

def connect_wifi():
    print("connect_wifi() called")

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm=0xa11140)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    display_message("Wifi connect to", WIFI_SSID)

    max_wait = 20
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print("Waiting for Wifi to connect")
        utime.sleep(0.3)

    if max_wait > 0:
        print("Wifi connected")
    else:
        print("Wifi not connected: timed out")

def display_message(line1="", line2="", line3=""):
    oled.fill(0)
    oled.text(line1, TEXT_X, TEXT_Y)
    oled.text(line2, TEXT_X, TEXT_Y + TEXT_Y_SPACE)
    oled.text(line3, TEXT_X, TEXT_Y + (TEXT_Y_SPACE * 2))
    oled.show()

def setup_display():
    global oled
    DISPLAY_WIDTH = 128
    DISPLAY_HEIGHT = 32

    i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)

    devices = i2c.scan()

    if devices:
        print("I2C found as follows.")
        for d in devices:
            print("     Device at address: " + hex(d))
    else:
        print("No I2C devices found.")
        sys.exit()

    print("     I2C Address      : " + hex(i2c.scan()[0]).upper())
    print("     I2C Configuration: " + str(i2c))

    oled = SSD1306_I2C(DISPLAY_WIDTH, DISPLAY_HEIGHT, i2c)
    oled.fill(0)
    oled.show()

def main():
    setup_display()

    # connect_wifi()

    display_message("Penmaenmawr", "forever")

if __name__ == "__main__":
    main()