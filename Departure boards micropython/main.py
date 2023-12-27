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
import uasyncio as asyncio

LINEONE_Y = 0
LINETWO_Y = 12
LINETHREE_Y = 24

DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 32
LINE_HEIGHT = 12

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
    oled.text(line1, TEXT_X, LINEONE_Y)
    oled.text(line2, TEXT_X, LINEONE_Y + TEXT_Y_SPACE)
    oled.text(line3, TEXT_X, LINEONE_Y + (TEXT_Y_SPACE * 2))
    oled.show()

def setup_display():
    global oled

    i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)

    devices = i2c.scan()

    if devices:
        print("I2C found as follows.")
        for d in devices:
            print("     Device at address: " + hex(d))
    else:
        print("No I2C devices found.")
        sys.exit()

    print("I2C Address      : " + hex(i2c.scan()[0]).upper())
    print("I2C Configuration: " + str(i2c))

    oled = SSD1306_I2C(DISPLAY_WIDTH, DISPLAY_HEIGHT, i2c)
    oled.fill(0)
    oled.show()

def clear_line(y):
    oled.fill_rect(0, y, DISPLAY_WIDTH, LINE_HEIGHT, 0)

async def display_clock():
    while True:
        clear_line(LINETHREE_Y)
        current_time = utime.localtime()
        time_string = "{:02d}:{:02d}:{:02d}".format(current_time[3], current_time[4], current_time[5])
        text_width = len(time_string) * 8  # 8 pixels per character
        x = (DISPLAY_WIDTH - text_width) // 2
        oled.text(time_string, x, LINETHREE_Y)
        oled.show()
        await asyncio.sleep(1)  # Update every second

async def scroll_text(text, y, speed=1):
    print(f"scroll_text() called with text: {text}")
    text_width = len(text) * 8  # 8 pixels per character
    for x in range(DISPLAY_WIDTH, -text_width, -speed):
        clear_line(y)
        oled.text(text, x, y)
        oled.show()
        await asyncio.sleep(0.01)  # Delay between frames

async def scroll_text_and_pause():
    print("scroll_text_and_pause() called")
    while True:
        await scroll_text("Please keep an eye on your belongings", LINETHREE_Y, 2)
        await asyncio.sleep(15)  # Wait for 5 seconds

async def main():
    clock_task = None
    scroll_task = None
    clock_mode = False # Setting to False will switch to clock mode first
    
    # connect_wifi()

    # display_message("Penmaenmawr", "forever")

    destinations = ["Llandudno J", "Penmaenmawr", "Bangor"]

    n=0
    while True:
        n = n+1
        print(f"main() loop: {n}")
        oled.text(destinations[0], 0, LINEONE_Y)
        oled.fill_rect(85, LINEONE_Y, DISPLAY_WIDTH, LINE_HEIGHT, 0)
        oled.text("12:12", 88, LINEONE_Y)

        oled.text(destinations[1], 0, LINETWO_Y)
        oled.fill_rect(85, LINETWO_Y, DISPLAY_WIDTH, LINE_HEIGHT, 0)
        oled.text("12:16", 88, LINETWO_Y)

        if clock_mode:
            print("Scroll it")
            if clock_task:
                clock_task.cancel()
            scroll_task = asyncio.create_task(scroll_text_and_pause())
        else:
            print("Clock it")
            if scroll_task:
                scroll_task.cancel()
            clock_task = asyncio.create_task(display_clock())

        clock_mode = not clock_mode
        await asyncio.sleep(8)  # Switch tasks every 5 seconds

if __name__ == "__main__":
    setup_display()
    asyncio.run(main())