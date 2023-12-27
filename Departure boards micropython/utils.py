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
from wifi_creds import WIFI_SSID, WIFI_PASSWORD

def connect_wifi():
    print("connect_wifi() called")

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm=0xa11140)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    max_wait = 20
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print("Waiting for Wifi to connect")
        utime.sleep(0.3)

    if max_wait > 0:
        print("Wifi connected")
    else:
        print("Wifi not connected: timed out")
    
def is_wifi_connected():
    is_it = network.WLAN(network.STA_IF).isconnected()
    # print(f"is_wifi_connected() called and returns {is_it}")
    return is_it

def disconnect_wifi():
    # print("disconnect_wifi() called")
    wlan = network.WLAN(network.STA_IF)
    wlan.disconnect()
    wlan.active(False)