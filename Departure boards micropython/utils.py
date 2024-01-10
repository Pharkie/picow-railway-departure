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
from config import LINEONE_Y
from globals import oled1

def connect_wifi():
    # print("connect_wifi() called")

    wlan = network.WLAN(network.STA_IF)
    
    # Reset connection
    if is_wifi_connected():
        disconnect_wifi()
    
    wlan.active(True)
    # wlan.config(pm=0xa11140)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    max_wait = 20
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print("Waiting for Wifi to connect")
        utime.sleep(0.6)

    if max_wait > 0:
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