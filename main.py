"""
Author: Adam Knowles
Version: 0.1
Name: main.py
Description: Mini Pico W OLED departure boards for model railway.
Uses 2 x SSD1306 OLED displays, 128x32 pixels, I2C.
Could maybe be adapted to work with other displays.

GitHub Repository: https://github.com/Pharkie/picow-railway-departure
Inspired by Stewart Watkiss - PenguinTutor (see upstream repo)
License: GNU General Public License (GPL)

User modules:
- config.py: Config variables for main program.
- rail_data.py: Functions for fetching and processing rail data.
- aws_api.py: Interface with AWS API. Signs a request with AWS credentials and an API key.
- display_utils.py: Functions for displaying information on the OLED screens.
- datetime_utils.py: Functions for working with date and time.
- utils.py: General utils not specific to a particular aspect of the program.

Also includes:
- aws_lambda_function.py: Lambda function to use with AWS Lambda as an API intermediary.
- sample_data.json: Sample data for offline mode, a JSON response saved from an API call.

Known issues: 
- ETIMEDOUT sometimes happens and crashes prog. Fix attempted.

"""

import asyncio
import sys
import gc
import io
from machine import I2C
import utime
import datetime_utils
import rail_data
from lib.ssd1306 import SSD1306_I2C
import display_utils
import config
import utils
from utils_logger import log_message


def set_global_exception():
    """
    Sets a global exception handler for the asyncio event loop.

    This function defines a handler that logs the exception message and the exception itself
    at the ERROR level, and then exits the program. It then gets the current event loop and
    sets the exception handler to the defined handler.
    """

    def handle_exception(loop, context): # pylint: disable=unused-argument
        exception = context.get('exception')
        s = io.StringIO()
        sys.print_exception(exception, s) # type: ignore # pylint: disable=no-member
        traceback_str = s.getvalue()
        log_message(
            f"Exiting. Caught unhandled global exception: {context['message']}, " +
            f"Type: {type(exception).__name__}, " +
            f"Details: {str(exception)}, " +
            f"Traceback: {traceback_str}", 
            level="ERROR"
        )
        sys.exit()

    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)


def initialize_oled(i2c, display_name):
    """
    This function initializes an OLED display.

    It first scans the I2C bus for devices. If devices are found, it prints the address of the
    first device. Then, it initializes an SSD1306 OLED display on the I2C bus, clears the display,
    and shows a loading message.

    Parameters:
    i2c: The I2C bus object.
    display_name: A string used to identify the display in print messages.

    Returns:
    oled: The initialized OLED display object, or None if initialization failed.
    """
    try:
        devices = i2c.scan()
        if devices:
            log_message(
                f"I2C found for {display_name}: {hex(i2c.scan()[0]).upper()}. Config: {str(i2c)}"
            )
        else:
            log_message(f"No I2C devices found on {display_name}.")

        oled = SSD1306_I2C(config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT, i2c)

        return oled
    except OSError as error:
        log_message(f"Failed to initialize {display_name}. Error: {str(error)}")
        return None


def setup_displays():
    """
    Sets up two OLED displays on two separate I2C buses.

    It first initializes the I2C buses. Then, it calls `initialize_oled` to initialize
    each display.
    If the second display fails to initialize, it prints a message to console and continues.

    Returns:
    setup_oled1, setup_oled2: The initialized OLED display objects. If a display failed to
    initialize, its value will be None.
    """
    i2c_oled1 = I2C(
        0,
        scl=config.OLED1_SCL_PIN,
        sda=config.OLED1_SDA_PIN,
        freq=100000,
        timeout=100000
    )

    i2c_oled2 = I2C(
        1,
        scl=config.OLED2_SCL_PIN,
        sda=config.OLED2_SDA_PIN,
        freq=100000,
        timeout=100000
    )

    setup_oled1 = initialize_oled(i2c_oled1, "oled1")
    setup_oled2 = initialize_oled(i2c_oled2, "oled2")

    if setup_oled2 is None:
        log_message("No oled2. Skipping operations on second screen.")

    return setup_oled1, setup_oled2


async def cycle_oled(oled, rail_data_instance, screen_number):
    """
    This coroutine manages the display of departures and travel alerts on an OLED screen.

    Parameters:
    oled: An OLED display object.
    rail_data_instance: An instance of the RailData class that provides the departure information.
    screen_number: The number of the screen (1 or 2).

    The coroutine retrieves the departures for the specified screen from the rail_data_instance.
    If there are departures, it displays the first and, if available, the second departure.
    If there are no departures, it displays "No departures".
    If there is a travel alert, it displays the alert.
    """
    while True:
        try:
            outdated_secs = max(config.DATA_OUTDATED_SECS, config.BASE_API_UPDATE_INTERVAL)
            if rail_data_instance.api_retry_secs >= outdated_secs:
            # Sustained API failure.
            # Time elapsed since update will be cumulative from time of failure
            # eg 5+10+20+40=75 secs
            # Number less than config.BASE_API_UPDATE_INTERVAL is ignored.
                await display_utils.clear_line(oled, config.LINEONE_Y)
                await display_utils.clear_line(oled, config.THICK_LINETWO_Y)

                async with oled.oled_lock:
                    oled.fd_oled.print_str("Train update failed", 0, config.LINEONE_Y)
                    oled.fd_oled.print_str(
                        f"Retry in {rail_data_instance.api_retry_secs} secs",
                        0,
                        config.THIN_LINETWO_Y,
                    )
                    oled.show()

                # No point rerunning this code every 3 seconds, so every 30.
                await asyncio.sleep(27)
            else:
                departures = None

                # if screen_number == 1: # Not used/replaced
                    # departures = rail_data_instance.oled1_departures
                if screen_number == 2:
                    departures = rail_data_instance.oled2_departures

                await display_utils.clear_line(oled, config.LINEONE_Y)
                await display_utils.clear_line(oled, config.THICK_LINETWO_Y)

                if departures:
                    await display_utils.display_first_departure(
                        oled,
                        rail_data_instance = rail_data_instance,
                        screen_number = screen_number
                    )

                    if len(departures) > 1:
                        await display_utils.display_second_departure(oled, departures[1])
                else:
                    await display_utils.display_no_departures(oled)

                if rail_data_instance.nrcc_message:
                    await display_utils.display_travel_alert(
                        oled, rail_data_instance.nrcc_message
                    )

            await asyncio.sleep(3)
        except Exception as error: # pylint: disable=broad-exception-caught
            log_message(
                f"cycle_oled caught error, will try to ignore: {str(error)}",
                level="ERROR",
            )

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
    set_global_exception()

    log_message(
        f"\n\n[Program started] {'OFFLINE' if config.OFFLINE_MODE else 'ONLINE'} mode.\n"
    )
    if not config.OFFLINE_MODE:
        log_message(f"Using API: {config.API_SOURCE}")

    gc.threshold(  # pylint: disable=no-member
        gc.mem_free() // 4 + gc.mem_alloc()  # pylint: disable=no-member
    )  # Set threshold for gc at 25% free memory
    gc.collect()

    # log("main() called")
    oled1, oled2 = setup_displays()

    if oled1 is None:
        log_message("Need oled on oled1, didn't find.", level="ERROR")
        raise RuntimeError("Need oled on oled1, didn't find.")

    await display_utils.display_init_message(oled1, oled2)
    utime.sleep(1)

    await display_utils.clear_display(oled1)
    if oled2:
        await display_utils.clear_display(oled2)

    if not config.OFFLINE_MODE:
        await utils.connect_wifi(oled1, oled2)

    rail_data_instance = rail_data.RailData()

    # At startup, run initial data gathering and wait
    # Sync the RTC with NTP or set a random time if in offline mode
    datetime_utils.sync_ntp()

    asyncio.create_task(display_utils.display_clock(oled1))
    if oled2:
        asyncio.create_task(display_utils.display_clock(oled2))

    if config.OFFLINE_MODE:
        rail_data_instance.get_offline_rail_data()
    else:
        try:
            # If this first API call fails, the program exits, since it has nothing to show.
            await rail_data_instance.get_online_rail_data()
        except Exception as caught_error: # pylint: disable=broad-exception-caught
            log_message(
                f"First API call failed. Exiting program: {caught_error}",
                level="ERROR",
            )
            raise
        asyncio.create_task(rail_data_instance.cycle_get_online_rail_data())

    asyncio.create_task(cycle_oled(oled1, rail_data_instance, 1))
    if oled2:
        asyncio.create_task(cycle_oled(oled2, rail_data_instance, 2))

    # Check if DST, every 60 seconds
    asyncio.create_task(utils.run_periodically(datetime_utils.check_dst, 60))

    # Run the above tasks until Exception or KeyboardInterrupt
    loop_counter = 0
    while True:
        loop_counter += 1
        gc.collect()
        log_message(
            f"Main loop cycle {loop_counter}. Free memory: {gc.mem_free()}"  # pylint: disable=no-member
        )
        await asyncio.sleep(45)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_message("[Program exiting cleanly] Keyboard Interrupt")
    # (I do want to catch all exceptions)
    except Exception as e: # pylint: disable=broad-exception-caught
        log_message(
            f"Unrecoverable error: {str(e)}",
            level="ERROR",
        )
        # machine.reset()  # Helpful?
    finally:
        asyncio.new_event_loop()  # Clear retained state
