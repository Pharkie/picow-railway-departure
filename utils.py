"""
Author: Adam Knowles
Version: 0.1
Name: utils.py
Description: General utils not specific to a particular aspect of the program.

GitHub Repository: https://github.com/Pharkie/AdamGalactic/
License: GNU General Public License (GPL)
"""

import asyncio
import network
import utime
import credentials
import config
import display_utils
from utils_logger import log_message


async def run_periodically(function, seconds):
    """
    Runs a function periodically.

    This function runs the provided function and then sleeps for a specified number of seconds.
    This process is repeated indefinitely.

    Parameters:
    function (function): The function to run.
    seconds (int or float): The number of seconds to sleep after running the function.

    Raises:
    TypeError: If the function is not callable or if seconds is not an int or float.
    """
    while True:
        await function()
        await asyncio.sleep(seconds)


async def connect_wifi(oled1=None, oled2=None):
    """
    Connects to the wifi network.

    This function tries to connect to the wifi network using the SSID and password from the
    credentials module. It waits for a maximum of WIFI_TIMEOUT seconds for the connection to
    be established. If the connection is successful, it logs a message and displays a success
    message on the OLED displays. If the connection fails or times out, it logs an error message,
    displays an error message on the OLED displays, and raises an OSError.

    Parameters:
    oled1 (SSD1306_I2C, optional): The first OLED display object. Defaults to None.
    oled2 (SSD1306_I2C, optional): The second OLED display object. Defaults to None.

    Raises:
    OSError: If the wifi connection fails or times out.
    """
    try:
        # log("connect_wifi() called")
        wlan = network.WLAN(network.STA_IF)
        wlan.active(False)
        wlan.active(True)
        wlan.connect(credentials.WIFI_SSID, credentials.WIFI_PASSWORD)

        max_wait = waited = config.WIFI_TIMEOUT
        while waited > 0:
            if wlan.isconnected():
                log_message("Wifi connected")
                await display_utils.both_screen_text(
                    oled1,
                    oled2,
                    "Wifi connected",
                    config.LINEONE_Y,
                    ":)",
                    config.THIN_LINETWO_Y,
                )
                # utime.sleep(1)
                # Clear screens but don't update display
                if oled1:
                    async with oled1.oled_lock:
                        oled1.fill(0)
                if oled2:
                    async with oled2.oled_lock:
                        oled2.fill(0)
                break
            elif wlan.status() in [
                network.STAT_WRONG_PASSWORD,
                network.STAT_NO_AP_FOUND,
                network.STAT_CONNECT_FAIL,
            ]:
                break  # Connection failed, no benefit to wait or retry

            log_message(
                f"Waiting for Wifi to connect {max_wait + 1 - waited}/{max_wait}"
            )
            await display_utils.both_screen_text(
                oled1,
                oled2,
                "Connecting wifi",
                config.LINEONE_Y,
                f"{max_wait + 1 - waited}/{max_wait}",
                config.THIN_LINETWO_Y,
            )
            waited -= 1
            utime.sleep(1)

        if not wlan.isconnected():
            log_message(
                f"Wifi not connected: timed out. wlan.status: {wlan.status()}",
                "ERROR",
            )
            await display_utils.both_screen_text(
                oled1,
                oled2,
                "Config = online",
                config.LINEONE_Y,
                "But no wifi :(",
                config.THIN_LINETWO_Y,
                "Stopping.",
                config.THIN_LINETHREE_Y,
            )
            raise OSError(
                f"Wifi not connected, timed out. wlan.status: {wlan.status()}"
            )
    except Exception as e:
        log_message(f"Exception while connecting WiFi: {e}", "ERROR")
        raise


def is_wifi_connected():
    """
    Checks if the device is connected to a wifi network.

    This function uses the network module to check if the device is connected to a wifi network.
    It returns True if the device is connected and False otherwise.

    Returns:
    bool: True if the device is connected to a wifi network, False otherwise.
    """
    is_it = network.WLAN(network.STA_IF).isconnected()
    # log(f"is_wifi_connected() called and returns {is_it}")
    return is_it


def disconnect_wifi():
    """
    Disconnects the device from the wifi network.

    This function uses the network module to disconnect the device from the wifi network and
    deactivate the network interface. It does not return anything.
    """
    # log("disconnect_wifi() called")
    wlan = network.WLAN(network.STA_IF)
    wlan.disconnect()
    wlan.active(False)
