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
import uasyncio as asyncio
import random
import datetime_utils
import utils
import ldbws
import config
from ssd1306 import SSD1306_I2C

# Set global variables
oled = None
nrcc_message = ""
departures_list = []

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

    oled = SSD1306_I2C(config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT, i2c)
    oled.fill(0)
    oled.text("Pico departures", 0, config.LINEONE_Y)
    oled.text("initilialising", 0, config.LINETWO_Y)
    oled.show()

def clear_display():
    oled.fill(0)
    oled.show()

def clear_line(y):
    oled.fill_rect(0, y, config.DISPLAY_WIDTH, config.LINE_HEIGHT, 0)

async def display_clock():
    while True:
        clear_line(config.LINETHREE_Y)
        current_time = utime.localtime()
        time_string = "{:02d}:{:02d}:{:02d}".format(current_time[3], current_time[4], current_time[5])
        text_width = len(time_string) * 8  # 8 pixels per character
        x = (config.DISPLAY_WIDTH - text_width) // 2
        oled.text(time_string, x, config.LINETHREE_Y)
        oled.show()
        await asyncio.sleep(1)  # Update every second

async def scroll_text(text, y, speed=1):
    # print(f"scroll_text() called with text: {text}")
    text_width = len(text) * 8  # 8 pixels per character
    for x in range(config.DISPLAY_WIDTH, -(text_width+1), -speed):
        clear_line(y)
        oled.text(text, x, y)
        oled.show()
        await asyncio.sleep(0.01)  # Delay between frames
    await asyncio.sleep(3) # Pause after finished scrolling

async def scroll_text_and_pause():
    # print("scroll_text_and_pause() called")

    info_strings = [
        "Be alert. See it. Say it. Sorted.",
        "Mind the gap",
        "Stand behind the yellow line",
        "Please have your ticket ready",
    ]

    while True:
        text = random.choice(info_strings)
        await scroll_text(text, config.LINETHREE_Y, 2)

async def refresh_ldbws_data():
    global nrcc_message, departures_list

    ldbws_api_data = await asyncio.create_task(ldbws.get_ldbws_api_data())
    nrcc_message = ldbws.get_nrcc_msg(ldbws_api_data) # TODO: Show this on the display
    departures_list = ldbws.get_departures(ldbws_api_data)

async def main():
    # print("aysnc main() called")
    clock_task = None
    scroll_task = None
    clock_mode = True # Setting to True shows message first
    
    clear_display()

    while True:
        if nrcc_message:
            print("Alert:", nrcc_message, "\n")

        if departures_list:
            for departure in departures_list:
                print("Train to:", departure["destination"])
                print("Departure time:", departure["time_due"])
                print("Platform:", departure["platform"])
                print()  # Add a newline between departures

            if len(departures_list) > 0:
                oled.text(departures_list[0]["destination"], 0, config.LINEONE_Y)
                oled.fill_rect(85, config.LINEONE_Y, config.DISPLAY_WIDTH, config.LINE_HEIGHT, 0)
                oled.text(departures_list[0]["time_due"], 88, config.LINEONE_Y)

            if len(departures_list) > 1:
                oled.text(departures_list[1]["destination"], 0, config.LINETWO_Y)
                oled.fill_rect(85, config.LINETWO_Y, config.DISPLAY_WIDTH, config.LINE_HEIGHT, 0)
                oled.text(departures_list[1]["time_due"], 88, config.LINETWO_Y)
        else:
            oled.text("No departures", 0, config.LINEONE_Y)

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

    # Set the sync tasks going
    asyncio.create_task(datetime_utils.sync_rtc_periodically())
    asyncio.create_task(ldbws.sync_ldbws_periodically())

    asyncio.run(main())