"""
Author: Adam Knowles
Version: 0.1
Name: utils.py
Description: General utils not specific to a particular thing

GitHub Repository: https://github.com/Pharkie/AdamGalactic/
License: GNU General Public License (GPL)
"""
import os
import network
import utime
import asyncio
import credentials
import config
import display_utils


def log_message(message, level="INFO"):
    levels = ["DEBUG", "INFO", "ERROR"]
    if levels.index(level) >= levels.index(config.LOG_LEVEL):
        max_log_size = 100 * 1024
        max_log_files = 2
        timestamp = utime.localtime(utime.time())
        formatted_timestamp = (
            f"{timestamp[0]:04d}-{timestamp[1]:02d}-{timestamp[2]:02d} "
            + f"{timestamp[3]:02d}:{timestamp[4]:02d}:{timestamp[5]:02d}"
        )
        log_message = f"{formatted_timestamp} [{level}]: {message}\n"

        print(log_message)

        log_filename = "rail_data_log.txt"
        try:
            if os.stat(log_filename)[6] > max_log_size:
                # If the log file is too big, rotate it.
                log_message += f"\nRotating log file {log_filename}. Max log size: {max_log_size} bytes, max rotated log files: {max_log_files}\n"

                try:
                    os.remove(f"{log_filename}.{max_log_files}")
                except OSError:
                    pass
                for i in range(max_log_files - 1, 0, -1):
                    try:
                        os.rename(f"{log_filename}.{i}", f"{log_filename}.{i+1}")
                    except OSError:
                        pass
                os.rename(log_filename, f"{log_filename}.1")
        except OSError:
            pass

        with open(log_filename, "a") as log_file:
            log_file.write(log_message)


async def run_periodically(function, seconds):
    while True:
        await function()
        await asyncio.sleep(seconds)


def connect_wifi(oled1=None, oled2=None):
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
                display_utils.both_screen_text(
                    oled1,
                    oled2,
                    "Wifi connected",
                    config.LINEONE_Y,
                    ":)",
                    config.THIN_LINETWO_Y,
                )
                utime.sleep(1)
                # Clear screens but don't update display
                if oled1:
                    oled1.fill(0)
                if oled2:
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
            display_utils.both_screen_text(
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
                f"Wifi not connected: timed out. wlan.status: {wlan.status()}", "ERROR"
            )
            display_utils.both_screen_text(
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
    is_it = network.WLAN(network.STA_IF).isconnected()
    # log(f"is_wifi_connected() called and returns {is_it}")
    return is_it


def disconnect_wifi():
    # log("disconnect_wifi() called")
    wlan = network.WLAN(network.STA_IF)
    wlan.disconnect()
    wlan.active(False)
