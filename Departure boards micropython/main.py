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
import uasyncio as asyncio
import urandom
import datetime_utils
import utils
import rail_data
from ssd1306 import SSD1306_I2C
from lib.fdrawer import FontDrawer
from display_utils import (
    clear_display,
    display_clock,
    display_no_departures,
    display_first_departure,
    display_second_departure,
    display_travel_alert
)
from config import (
    LINEONE_Y,
    THIN_LINETWO_Y,
    DISPLAY_WIDTH,
    DISPLAY_HEIGHT,
    offline_mode
)

def initialize_oled(i2c, display_name):
    """
    This function initializes an OLED display.

    It first scans the I2C bus for devices. If devices are found, it prints the address of the first device.
    Then, it initializes an SSD1306 OLED display on the I2C bus, clears the display, and shows a loading message.

    Parameters:
    i2c: The I2C bus object.
    display_name: A string used to identify the display in print messages.

    Returns:
    oled: The initialized OLED display object, or None if initialization failed.
    """
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
    """
    Sets up two OLED displays on two separate I2C buses.

    It first initializes the I2C buses. Then, it calls `initialize_oled` to initialize each display.
    If the second display fails to initialize, it prints a message to console and continues.

    Returns:
    setup_oled1, setup_oled2: The initialized OLED display objects. If a display failed to initialize, its value will be None.
    """
    i2c_oled1 = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)
    i2c_oled2 = I2C(1, scl=Pin(19), sda=Pin(18), freq=200000)

    setup_oled1 = initialize_oled(i2c_oled1, "oled1")
    setup_oled2 = initialize_oled(i2c_oled2, "oled2")

    if setup_oled2 is None:
        print("No oled2. Skipping operations on second screen.")

    return setup_oled1, setup_oled2

async def run_periodically(func, wait_seconds):
    """
    This coroutine runs a given function periodically at a given interval.

    Parameters:
    func: The function to run.
    interval: The interval (in seconds) at which to run the function.
    """
    await asyncio.sleep(wait_seconds)
    while True:
        await func()
        await asyncio.sleep(wait_seconds)
    
async def run_oled(oled, fd_oled, departures, nrcc_message, clock_task):
    """
    This coroutine manages the display of departures and travel alerts on an OLED screen.

    Parameters:
    oled: An OLED display object.
    fd_oled: A Fontdrawer object for the OLED display.
    departures: A list of departures to display.
    nrcc_message: A travel alert message to display.
    clock_task: An asyncio Task object for displaying the clock.

    If there are departures, it displays the first departure and, if available, the second departure.
    If there are no departures, it displays "No departures".
    If there is a travel alert, it cancels the clock task, displays the alert, and then restarts the clock task.
    """
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
    """
    Initializes and manages the tasks for the OLED displays.

    It first synchronizes the real-time clock and fetches the initial rail data. 
    Then, if not in offline mode, it sets up tasks to periodically synchronize the clock 
    and update the rail data at random intervals.

    Parameters:
    oled1: The first OLED display object.
    oled2: The second OLED display object.

    This function is a coroutine and should be used with `await` or `asyncio.create_task()`.
    """
    # print("main() called")
    rail_data_instance = rail_data.RailData()

    # At startup, run both functions once and wait
    await datetime_utils.sync_rtc()
    await rail_data_instance.get_rail_data()

    # Set them to run in the background from now on
    if not offline_mode:
        # TODO: Make just do the DST check not the clock sync
        asyncio.create_task(run_periodically(datetime_utils.sync_rtc, urandom.randint(60, 6000)))
        # Update once a minute
        asyncio.create_task(run_periodically(rail_data_instance.get_rail_data, 60))

    clear_display(oled1)
    clear_display(oled2)

    fd_oled1 = FontDrawer(frame_buffer=oled1, font_name = 'dejav_m10')
    fd_oled2 = FontDrawer(frame_buffer=oled2, font_name = 'dejav_m10')

    oled1_clock_task = asyncio.create_task(display_clock(oled1, fd_oled1))
    oled2_clock_task = asyncio.create_task(display_clock(oled2, fd_oled2))

    oled1_task, oled2_task = None, None

    while True:
        if not oled1_task or oled1_task.done():
            oled1_task = asyncio.create_task(
                run_oled(
                    oled1,
                    fd_oled1,
                    rail_data_instance.oled1_departures,
                    rail_data_instance.nrcc_message,
                    oled1_clock_task
                )
            )
        if oled2 and (not oled2_task or oled2_task.done()):
            oled2_task = asyncio.create_task(
                run_oled(
                    oled2,
                    fd_oled2,
                    rail_data_instance.oled2_departures,
                    rail_data_instance.nrcc_message,
                    oled2_clock_task
                )
            )
        await asyncio.sleep(1) # Without this, nothing has time to run

if __name__ == "__main__":
    oled1, oled2 = setup_displays()

    if not offline_mode:
        utils.connect_wifi(oled1)

    asyncio.run(main(oled1, oled2))
