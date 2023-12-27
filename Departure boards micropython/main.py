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
import utime
from ssd1306 import SSD1306_I2C
import uasyncio as asyncio
import random
import datetime_utils
import utils

LINEONE_Y = 0
LINETWO_Y = 12
LINETHREE_Y = 24

DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 32
LINE_HEIGHT = 12

# Set as global
oled = None

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
    for x in range(DISPLAY_WIDTH, -(text_width+1), -speed):
        clear_line(y)
        oled.text(text, x, y)
        oled.show()
        await asyncio.sleep(0.01)  # Delay between frames
    await asyncio.sleep(3) # Pause after finished scrolling

async def scroll_text_and_pause():
    print("scroll_text_and_pause() called")

    info_strings = [
        "Please keep an eye on your belongings",
        "Mind the gap",
        "Stand clear of the doors",
        "The next train does not stop here - stand back",
        "Please stand back from the platform edge",
        "Please move down inside the car",
    ]

    while True:
        text = random.choice(info_strings)
        await scroll_text(text, LINETHREE_Y, 2)

async def main():
    clock_task = None
    scroll_task = None
    clock_mode = False # Setting to False will switch to clock mode first
    
    destinations = ["Llandudno J", "Penmaenmawr", "Bangor"]

    while True:
        oled.text(destinations[0], 0, LINEONE_Y)
        oled.fill_rect(85, LINEONE_Y, DISPLAY_WIDTH, LINE_HEIGHT, 0)
        oled.text("12:12", 88, LINEONE_Y)

        oled.text(destinations[1], 0, LINETWO_Y)
        oled.fill_rect(85, LINETWO_Y, DISPLAY_WIDTH, LINE_HEIGHT, 0)
        oled.text("12:16", 88, LINETWO_Y)

        if clock_mode:
            if clock_task:
                clock_task.cancel()
            scroll_task = asyncio.create_task(scroll_text_and_pause())
        else:
            if scroll_task:
                scroll_task.cancel()
            clock_task = asyncio.create_task(display_clock())

        clock_mode = not clock_mode
        await asyncio.sleep(8)  # Switch tasks every X seconds

if __name__ == "__main__":
    setup_display()
    utils.connect_wifi()

    sync_ntp_task = asyncio.create_task(datetime_utils.sync_rtc_periodically())

    asyncio.run(main())