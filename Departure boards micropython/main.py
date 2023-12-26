"""
Author: Adam Knowles
Version: 0.1
Name: main.py
Description: Mini OLED departure boards for model railway

GitHub Repository: https://github.com/Pharkie/picow-railway-departure
Based on work by Stewart Watkiss - PenguinTutor
License: GNU General Public License (GPL)
"""
try:
    from machine import Pin, I2C # Pin, I2C # type: ignore
    import utime # type: ignore
    import ujson # type: ignore
    import urequests # type: ignore
except ImportError:
    print("Error: Unable to import 'machine', 'utime', or 'ujson' module")

from ssd1306 import SSD1306_I2C
import network
from wifi_creds import WIFI_SSID, WIFI_PASSWORD

URL = "http://192.168.0.2:8080/departures.py?platform="

TEXT_X = 0 # start point for text in x-dir
TEXT_Y = 0 # start point for text in y-dir
TEXT_Y_SPACE = 12 # space between text in y-dir

oled = None
oled1 = None
# Turn wifi on or off
try_wifi = True

def connect_wifi():
    print("connect_wifi() called")

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm=0xa11140)  # Turn WiFi power saving off for some slow APs # type: ignore
    wlan.connect(WIFI_SSID, WIFI_PASSWORD) # type: ignore

    display_message ("Wifi connect to", WIFI_SSID)

    # Wait for connect success or failure
    max_wait = 20
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print("Waiting for Wifi to connect")
        # Doesn't use async await to block the clock from display updates until the sync is complete
        utime.sleep(0.3)

    if max_wait > 0:
        print("Wifi connected")
    else:
        print("Wifi not connected: timed out")

def main():
    global oled, oled1, try_wifi
    WIDTH  = 128 # SSD1306 horizontal resolution
    HEIGHT = 32   # SSD1306 vertical resolution

    # Scan for devices and print out any addresses found
    devices = i2c.scan()

    if devices:
        print("I2C found as follows.")
        for d in devices:
            print("     Device at address: " + hex(d))
    else:
        print("No I2C devices found.")
        sys.exit()

    i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)  # start I2C on I2C0 (GP 16/17) physical 21/22
    #i2c_dev1 = I2C(1,scl=Pin(19),sda=Pin(18),freq=200000)  # start I2C on I2C1 (GP 18/19) physical 24/25

    oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)  # Init oled display
    # Omit second display for now
    # oled1 = SSD1306_I2C(width, height, i2c_dev1) # oled controller

    print("I2C Address      : " + hex(i2c.scan()[0]).upper())   # Display device address
    print("I2C Configuration: " + str(i2c))                         # Display I2C config

    connect_wifi()
    
    while True:
        display_message (*get_train_list(0), 0)
        display_message (*get_train_list(1), 1)
        # check every 30 seconds
        utime.sleep (30)
        
def display_message (line1 = "", line2 = "", line3 = "", display=-1):
    # no display specified - use both
    if (display == -1):
        _disp_msg(line1,line2,line3,0)
        _disp_msg(line1,line2,line3,1)
    elif (display == 1):
        _disp_msg(line1,line2,line3,1)
    else:
        _disp_msg(line1,line2,line3,0)

# This internal method updates a single display only, it doesn't affect other displays.
def _disp_msg(line1, line2, line3, display):
    global oled, oled1

    oled = None  # Assign a value to oled
    oled1 = None  # Assign a value to oled1
    
    if display == 1:
        disp = oled1
    else:
        disp = oled

    disp.fill(0)
    disp.text(line1, TEXT_X, TEXT_Y)
    disp.text(line2, TEXT_X, TEXT_Y + TEXT_Y_SPACE)
    disp.text(line3, TEXT_X, TEXT_Y + (TEXT_Y_SPACE * 2))
    disp.show()

# Returns 3 lines of text 
def get_train_list(platform=0):
    # Generic error message if no other messages
    text_list = ["Departure board", "Out of order", "**********"]
    
    if try_wifi:
        try:
            this_url = URL+str(platform)
            request = urequests.get(this_url)
            #print (request.content)
            train_data = ujson.loads(request.content)
            #print (str(train_data))
            request.close()
            
        except Exception as e:
            print(f"Error retrieving from url {URL}{platform}")
            print(f"An error occurred: {str(e)}")
            return text_list
        
        # Some limited format checking:trims entries that don't fit

        # Format lines 16 characters per line
        # This is less than other displays so only show time and destination
        # time[5], space, destination [10]
        if 'train1' in train_data:
            text_list[0] = train_data['train1'][0][:5]
            text_list[0] += " "
            text_list[0] += train_data['train1'][1][:10]
            
        if 'train2' in train_data:
            text_list[1] = train_data['train2'][0][:5]
            text_list[1] += " "
            text_list[1] += train_data['train2'][1][:10]
            
        # time is a single entry - 
        if 'time' in train_data:
            # 5 spaces
            text_list[2] = "     "
            text_list[2] += train_data['time'][:5]
            
    return text_list
    
if __name__ == "__main__":
    print("main.py called")
    main()