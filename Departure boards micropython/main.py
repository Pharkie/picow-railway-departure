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
import time
import datetime_utils
import utils
import rail_data
import urandom
from ssd1306 import SSD1306_I2C
import framebuf
from lib.fdrawer import FontDrawer
from config import LINEONE_Y, THIN_LINETWO_Y, THIN_LINETHREE_Y, THIN_LINE_HEIGHT, THICK_LINE_HEIGHT, THICK_LINETWO_Y, THICK_LINETHREE_Y, THICK_CHAR_WIDTH
from config import DISPLAY_WIDTH, DISPLAY_HEIGHT, THIN_CHAR_WIDTH, offline_mode
from display_utils import clear_display, display_clock, display_no_departures, display_first_departure, display_second_departure
from display_utils import display_travel_alert

def initialize_oled(i2c, display_name):
    try:
        devices = i2c.scan()
        if devices:
            print(f"I2C found for {display_name}: {hex(i2c.scan()[0]).upper()}. Config: {str(i2c)}")
        else:
            print(f"No I2C devices found on {display_name}.")

        oled = SSD1306_I2C(DISPLAY_WIDTH, DISPLAY_HEIGHT, i2c)
        oled.fill(0)
        oled.text("Loading", 0, LINEONE_Y)
        oled.text("Pico departures", 0, THIN_LINETWO_Y)
        oled.show()

        return oled
    except Exception as e:
        print(f"Failed to initialize {display_name}. Error: {str(e)}")
        return None

def setup_displays():
    i2c_oled1 = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)
    i2c_oled2 = I2C(1, scl=Pin(19), sda=Pin(18), freq=200000)

    oled1 = initialize_oled(i2c_oled1, "oled1")
    oled2 = initialize_oled(i2c_oled2, "oled2")

    if oled2 is None:
        print("No oled2. Skipping operations on second screen.")

    return oled1, oled2

async def run_periodically(func, wait_seconds):
    await asyncio.sleep(wait_seconds)
    while True:
        await func()
        await asyncio.sleep(wait_seconds)
    
async def run_oled(oled, fd_oled, departures, nrcc_message, clock_task):
    # Show first departure for each screen on line one, and scroll the calling points on line two
    if len(departures) > 0:
        await display_first_departure(oled, fd_oled, departures)
    else:
        await display_no_departures(oled, fd_oled)

    # If there is a second departure for this screen, show it on line two
    if len(departures) > 1:
        await display_second_departure(oled, fd_oled, departures)

    if nrcc_message:
        clock_task.cancel()
        await display_travel_alert(oled, fd_oled, nrcc_message)
        clock_task = asyncio.create_task(display_clock(oled, fd_oled))
    else:
        await asyncio.sleep(3)

async def main(oled1, oled2):
    # print("main() called")
    rail_data_instance = rail_data.RailData()
  
    # At startup, run both functions once and wait
    await datetime_utils.sync_rtc()
    await rail_data_instance.get_rail_data()

    # Set them to run in the background from now on
    if not offline_mode:
        asyncio.create_task(run_periodically(datetime_utils.sync_rtc, urandom.randint(60, 6000)))  # TODO: Make just do the DST check not the clock sync
        asyncio.create_task(run_periodically(rail_data_instance.get_rail_data, urandom.randint(59, 119)))  # Run every 1-2 minutes

    clear_display(oled1)
    clear_display(oled2)

    fd_oled1 = FontDrawer(frame_buffer=oled1, font_name = 'dejav_m10')
    fd_oled2 = FontDrawer(frame_buffer=oled2, font_name = 'dejav_m10')

    oled1_clock_task = asyncio.create_task(display_clock(oled1, fd_oled1))
    oled2_clock_task = asyncio.create_task(display_clock(oled2, fd_oled2))

    oled1_task, oled2_task = None, None
    
    while True:
        if not oled1_task or oled1_task.done():
            oled1_task = asyncio.create_task(run_oled(oled1, fd_oled1, rail_data_instance.oled1_departures, rail_data_instance.nrcc_message, oled1_clock_task))
        if oled2 and (not oled2_task or oled2_task.done()):
            oled2_task = asyncio.create_task(run_oled(oled2, fd_oled2, rail_data_instance.oled2_departures, rail_data_instance.nrcc_message, oled2_clock_task))
        await asyncio.sleep(1) # Without this, nothing has time to run

if __name__ == "__main__":
    oled1, oled2 = setup_displays()

    if not offline_mode:
        utils.connect_wifi(oled1)

    asyncio.run(main(oled1, oled2))