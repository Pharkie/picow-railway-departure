"""
Author: Adam Knowles
Version: 0.1
Name: main.py
Description: Mini Pico W OLED departure boards for model railway

GitHub Repository: https://github.com/Pharkie/picow-railway-departure
Based on work by Stewart Watkiss - PenguinTutor
License: GNU General Public License (GPL)

Known issues: doesn't handle DST change while device is running, since only checks at startup.

"""
from machine import I2C
import uasyncio as asyncio
import utime
import datetime_utils
import utils
import gc
import rail_data
from lib.ssd1306 import SSD1306_I2C
from lib.fdrawer import FontDrawer
import display_utils
import config
# from logger import log

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

        oled = SSD1306_I2C(config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT, i2c)

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
    i2c_oled1 = I2C(0, scl=config.OLED1_SCL_PIN, sda=config.OLED1_SDA_PIN, freq=200000)
    i2c_oled2 = I2C(1, scl=config.OLED2_SCL_PIN, sda=config.OLED2_SDA_PIN, freq=200000)

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
    
async def cycle_oled(oled, fd_oled, rail_data_instance, screen_number):
    """
    This coroutine manages the display of departures and travel alerts on an OLED screen.

    Parameters:
    oled: An OLED display object.
    fd_oled: A Fontdrawer object for the OLED display.
    rail_data_instance: An instance of the RailData class that provides the departure information.
    screen_number: The number of the screen (1 or 2).

    The coroutine retrieves the departures for the specified screen from the rail_data_instance. 
    If there are departures, it displays the first and, if available, the second departure. 
    If there are no departures, it displays "No departures". 
    If there is a travel alert, it displays the alert.
    """
    while True:
        if screen_number == 1:
            departures = rail_data_instance.oled1_departures
        elif screen_number == 2:
            departures = rail_data_instance.oled2_departures

        if departures:
            await display_utils.display_first_departure(oled, fd_oled, departures[0])

            if len(departures) > 1:
                await display_utils.display_second_departure(oled, fd_oled, departures[1])
        else:
            await display_utils.display_no_departures(oled, fd_oled)

        if rail_data_instance.nrcc_message:
            await display_utils.display_travel_alert(oled, fd_oled, rail_data_instance.nrcc_message)
            
        await asyncio.sleep(3)

async def main():
    """
    The main coroutine.

    Sets up OLED displays, initializes rail data, and creates tasks to 
    display the clock, update rail data, and cycle through rail data on 
    the displays. If not in offline mode, it also connects to Wi-Fi and 
    updates rail data every 60 seconds.

    Parameters:
        None

    Returns:
        None 
    """
    gc.threshold(gc.mem_free() // 4 + gc.mem_alloc()) # Set threshold for gc at 25% free memory
    gc.collect()

    # print("main() called")
    oled1, oled2 = setup_displays()

    # dejav_m10.bin must be in the root directory
    fd_oled1 = FontDrawer(frame_buffer=oled1, font_name = 'dejav_m10') 
    fd_oled2 = FontDrawer(frame_buffer=oled2, font_name = 'dejav_m10')

    display_utils.display_init_message(oled1, oled2, fd_oled1, fd_oled2)
    utime.sleep(2)
    display_utils.clear_display(oled1)
    display_utils.clear_display(oled2)

    if not config.offline_mode:
        utils.connect_wifi(oled1, oled2, fd_oled1, fd_oled2)

    rail_data_instance = rail_data.RailData()

    # At startup, run both functions once and wait
    await datetime_utils.sync_rtc()
    await rail_data_instance.get_rail_data()

    asyncio.create_task(display_utils.display_clock(oled1, fd_oled1))
    asyncio.create_task(display_utils.display_clock(oled2, fd_oled2))

    # update_rail_data_task = asyncio.create_task(run_periodically(rail_data_instance.get_rail_data, 10)) # For testing
    if not config.offline_mode: 
        asyncio.create_task(run_periodically(rail_data_instance.get_rail_data, 60))

    asyncio.create_task(cycle_oled(oled1, fd_oled1, rail_data_instance, 1))
    asyncio.create_task(cycle_oled(oled2, fd_oled2, rail_data_instance, 2))

    # Run the above tasks until Exception or KeyboardInterrupt
    while True:
        gc.collect() # Fixes a memory leak someplace
        print(f"Main loop cycle. Free memory: {gc.mem_free()}")
        await asyncio.sleep(50)

if __name__ == "__main__":
    asyncio.run(main())
