"""
Author: Adam Knowles
Version: 0.1
Name: utils.py
Description: General utils not specific to a particular thing

GitHub Repository: https://github.com/Pharkie/AdamGalactic/
License: GNU General Public License (GPL)
"""
import network # type: ignore
import utime # type: ignore
import credentials
import config
import display_utils

def connect_wifi(oled1=None, oled2=None, fd_oled1=None, fd_oled2=None):
    # print("connect_wifi() called")
    global offline_mode

    wlan = network.WLAN(network.STA_IF)

    # Deactivate and then reactivate the WiFi interface for a complete reset
    wlan.active(False)
    utime.sleep(1)  # Wait a bit for the interface to deactivate
    wlan.active(True)
    utime.sleep(1)  # Wait a bit for the interface to activate

    # Reset connection
    if is_wifi_connected():
        disconnect_wifi()

    wlan.config(pm=wlan.PM_NONE)
    wlan.config(txpower=18)
    # wlan.config(pm=0xa11140)
    wlan.connect(credentials.WIFI_SSID, credentials.WIFI_PASSWORD)

    max_wait = waited = config.WIFI_TIMEOUT
    while waited > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        print(f"Waiting for Wifi to connect {max_wait + 1 - waited}/{max_wait}")
        display_utils.both_screen_text(oled1, oled2, fd_oled1, fd_oled2, "Connecting wifi", config.LINEONE_Y, f"{max_wait + 1 - waited}/{max_wait}", config.THIN_LINETWO_Y)
        waited -= 1
        utime.sleep(1)

    if network.WLAN(network.STA_IF).isconnected():
        print("Wifi connected")
        display_utils.both_screen_text(oled1, oled2, fd_oled1, fd_oled2, "Wifi connected", config.LINEONE_Y, ":)", config.THIN_LINETWO_Y)
    else:
        print("Wifi not connected: timed out")
        offline_mode = True
        display_utils.both_screen_text(oled1, oled2, fd_oled1, fd_oled2, "No wifi :(", config.LINEONE_Y, "Switching to", config.THIN_LINETWO_Y, "offline mode", config.THIN_LINETHREE_Y)

    utime.sleep(1)
    # Clear screens after (but don't update display)
    if oled1:
        oled1.fill(0)
    if oled2:
        oled2.fill(0)

def is_wifi_connected():
    is_it = network.WLAN(network.STA_IF).isconnected()
    # print(f"is_wifi_connected() called and returns {is_it}")
    return is_it

def disconnect_wifi():
    # print("disconnect_wifi() called")
    wlan = network.WLAN(network.STA_IF)
    wlan.disconnect()
    wlan.active(False)
