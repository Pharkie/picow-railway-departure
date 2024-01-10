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
import rail_data
import urandom
from ssd1306 import SSD1306_I2C
from config import LINEONE_Y, LINETWO_Y, LINETHREE_Y, DISPLAY_WIDTH, DISPLAY_HEIGHT, LINE_HEIGHT, INFO_STRINGS
from globals import oled1

def setup_display():
    global oled1

    i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)

    devices = i2c.scan()

    if devices:
        print("I2C found as follows.")
        for d in devices:
            print("     Device at address: " + hex(d))
    else:
        print("No I2C devices found.")

    print("I2C Address      : " + hex(i2c.scan()[0]).upper())
    print("I2C Configuration: " + str(i2c))

    oled1 = SSD1306_I2C(DISPLAY_WIDTH, DISPLAY_HEIGHT, i2c)
    oled1.fill(0)
    oled1.text("Loading", 0, LINEONE_Y)
    oled1.text("Pico departures", 0, LINETWO_Y)
    oled1.show()

def clear_display():
    oled1.fill(0)
    oled1.show()

def clear_line(y):
    oled1.fill_rect(0, y, DISPLAY_WIDTH, LINE_HEIGHT, 0)

async def display_clock():
    while True:
        clear_line(LINETHREE_Y)
        current_time = utime.localtime()
        time_string = "{:02d}:{:02d}:{:02d}".format(current_time[3], current_time[4], current_time[5])
        text_width = len(time_string) * 8  # 8 pixels per character
        x = (DISPLAY_WIDTH - text_width) // 2
        oled1.text(time_string, x, LINETHREE_Y)
        oled1.show()
        await asyncio.sleep(1)  # Update every second

async def scroll_text(text, y, speed=2):
    # print(f"scroll_text() called with text: {text}")
    text_width = len(text) * 8  # 8 pixels per character
    for x in range(DISPLAY_WIDTH, -(text_width+1), -speed):
        clear_line(y)
        oled1.text(text, x, y)
        oled1.show()
        await asyncio.sleep(0.01)  # Delay between frames
    await asyncio.sleep(3) # Pause after finished scrolling

async def scroll_text_and_pause():
    # print("scroll_text_and_pause() called")
    while True:
        text = random.choice(INFO_STRINGS)
        await scroll_text(text, LINETHREE_Y, 2)

async def run_periodically(func, wait_seconds):
    await asyncio.sleep(wait_seconds)
    while True:
        await func()
        await asyncio.sleep(wait_seconds)

def format_calling_points(departure):
    calling_points = departure['subsequentCallingPoints']
    if not calling_points:
        return "Calling at destination only"
    
    # Format all but the last calling point
    calling_points_text = "Calling at: " + ', '.join(
        f"{calling_point['locationName']} ({calling_point['time_due']})"
        for calling_point in calling_points[:-1]
    )
    
    # Add 'and' before the last calling point
    last_calling_point = f"{calling_points[-1]['locationName']} ({calling_points[-1]['time_due']})"

    if calling_points_text:
        calling_points_text += f" and {last_calling_point}"
    else:
        calling_points_text = f"Calling at: {last_calling_point}"
    
    return calling_points_text

async def main():
    # print("aysnc main() called")
    rail_data_instance = rail_data.RailData()
    
    clock_task = None
    scroll_task = None
    call_point_task = None
    clock_mode = True # Setting to True shows message first
    
    # At startup, run both functions once and wait
    await datetime_utils.sync_rtc()
    await rail_data_instance.get_rail_data()

    # Set them to run in the background from now on
    asyncio.create_task(run_periodically(datetime_utils.sync_rtc, urandom.randint(60, 6000)))  # TODO: Make just do the DST check not the clock sync
    asyncio.create_task(run_periodically(rail_data_instance.get_rail_data, urandom.randint(59, 119)))  # Run every 1-2 minutes

    clear_display()

    while True:
        if rail_data_instance.nrcc_message:
            print("NRCC alert:", rail_data_instance.nrcc_message, "\n")

        if rail_data_instance.departures_list is not None:
            if len(rail_data_instance.departures_list) > 0:
                oled1.text(rail_data_instance.departures_list[0]["destination"], 0, LINEONE_Y)
                oled1.fill_rect(85, LINEONE_Y, DISPLAY_WIDTH, LINE_HEIGHT, 0)
                oled1.text(rail_data_instance.departures_list[0]["time_due"], 88, LINEONE_Y)
                # print(format_calling_points(rail_data_instance.departures_list[0]))
                if not call_point_task or call_point_task.done():
                    call_point_task = asyncio.create_task(scroll_text(format_calling_points(rail_data_instance.departures_list[0]), LINETWO_Y, 4))

            # if len(rail_data_instance.departures_list) > 1:
            #     oled.text(rail_data_instance.departures_list[1]["destination"], 0, LINETWO_Y)
            #     oled.fill_rect(85, LINETWO_Y, DISPLAY_WIDTH, LINE_HEIGHT, 0)
            #     oled.text(rail_data_instance.departures_list[1]["time_due"], 88, LINETWO_Y)
            
        else:
            oled1.text("No departures", 0, LINEONE_Y)

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

    asyncio.run(main())