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
from config import WIFI_TIMEOUT

def connect_wifi():
    # print("connect_wifi() called")

    wlan = network.WLAN(network.STA_IF)
    
    # Deactivate and then reactivate the WiFi interface for a complete reset
    wlan.active(False)
    utime.sleep(1)  # Wait a bit for the interface to deactivate
    wlan.active(True)
    utime.sleep(1)  # Wait a bit for the interface to activate

    # Reset connection
    if is_wifi_connected():
        disconnect_wifi()
    
    # wlan.config(pm=0xa11140)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    max_wait = waited = WIFI_TIMEOUT
    while waited > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        print(f"Waiting for Wifi to connect {max_wait + 1 - waited}/{max_wait}")
        waited -= 1
        utime.sleep(1)

    if network.WLAN(network.STA_IF).isconnected():
        print("Wifi connected")
        # oled1.fill(0)
        # oled1.text("Wifi connected", 0, LINEONE_Y)
        # oled1.show()
    else:
        print("Wifi not connected: timed out")
        # oled1.fill(0)
        # oled1.text("Wifi not connected", 0, LINEONE_Y)
        # oled1.show()
    
def is_wifi_connected():
    is_it = network.WLAN(network.STA_IF).isconnected()
    # print(f"is_wifi_connected() called and returns {is_it}")
    return is_it

def disconnect_wifi():
    # print("disconnect_wifi() called")
    wlan = network.WLAN(network.STA_IF)
    wlan.disconnect()
    wlan.active(False)