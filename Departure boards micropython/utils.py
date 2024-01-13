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
from credentials import WIFI_SSID, WIFI_PASSWORD
from config import WIFI_TIMEOUT, LINEONE_Y, THIN_LINETWO_Y, THIN_LINETHREE_Y, offline_mode, THIN_LINE_HEIGHT, THIN_CHAR_WIDTH

def connect_wifi(oled_display=None):
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

    wlan.config(pm=0xa11140)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    max_wait = waited = WIFI_TIMEOUT
    while waited > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        print(f"Waiting for Wifi to connect {max_wait + 1 - waited}/{max_wait}")
        oled_display.fill(0)
        oled_display.text("Connecting wifi", 0, LINEONE_Y)
        oled_display.text(f"{max_wait + 1 - waited}/{max_wait}", 50, THIN_LINETWO_Y)
        oled_display.show()
        waited -= 1
        utime.sleep(1)

    oled_display.fill(0)
    if network.WLAN(network.STA_IF).isconnected():
        print("Wifi connected")
        oled_display.text("Wifi connected", 0, LINEONE_Y)
        oled_display.text(":)", 56, THIN_LINETWO_Y)
    else:
        print("Wifi not connected: timed out")
        offline_mode = True
        oled_display.text("No wifi :(", 24, LINEONE_Y)
        oled_display.text("Switching to", 0, THIN_LINETWO_Y)
        oled_display.text("offline mode", 0, THIN_LINETHREE_Y)
    oled_display.show()
    utime.sleep(1)

def is_wifi_connected():
    is_it = network.WLAN(network.STA_IF).isconnected()
    # print(f"is_wifi_connected() called and returns {is_it}")
    return is_it

def disconnect_wifi():
    # print("disconnect_wifi() called")
    wlan = network.WLAN(network.STA_IF)
    wlan.disconnect()
    wlan.active(False)
