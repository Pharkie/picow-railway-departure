"""
Author: Adam Knowles
Version: 0.1
Name: main.py
Description: Mini Pico W OLED departure boards for model railway

GitHub Repository: https://github.com/Pharkie/picow-railway-departure
Based on work by Stewart Watkiss - PenguinTutor
License: GNU General Public License (GPL)
"""
from machine import Pin, I2C
import utime
import uasyncio as asyncio
import time
import datetime_utils
import utils
import rail_data
import urandom
from ssd1306 import SSD1306_I2C
from config import LINEONE_Y, LINETWO_Y, LINETHREE_Y, DISPLAY_WIDTH, DISPLAY_HEIGHT, LINE_HEIGHT, CHAR_WIDTH
from my_global_vars import oled1

def setup_display():
    global oled1

    i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)

    devices = i2c.scan()

    if devices:
        print("I2C found as follows.")
        for d in devices:
            print("     Device at address: " + hex(d))
    else:
        print("No I2C devices found.")

    print("I2C Address      : " + hex(i2c.scan()[0]).upper())
    print("I2C Configuration: " + str(i2c))

    oled1 = SSD1306_I2C(DISPLAY_WIDTH, DISPLAY_HEIGHT, i2c)
    oled1.fill(0)
    oled1.text("Loading", 0, LINEONE_Y)
    oled1.text("Pico departures", 0, LINETWO_Y)
    oled1.show()

def clear_display():
    oled1.fill(0)
    oled1.show()

def clear_line(y):
    oled1.fill_rect(0, y, DISPLAY_WIDTH, LINE_HEIGHT, 0)

async def display_clock():
    time_string = "{:02d}:{:02d}:{:02d}"
    text_width = len(time_string.format(0, 0, 0)) * 8  # 8 pixels per character
    x = (DISPLAY_WIDTH - text_width) // 2

    while True:
        # Clear only the area where the time is displayed
        oled1.fill_rect(x, LINETHREE_Y, text_width, 8, 0)

        current_time = utime.localtime()
        oled1.text(time_string.format(current_time[3], current_time[4], current_time[5]), x, LINETHREE_Y)
        oled1.show()
        await asyncio.sleep(1)  # Update every second

async def display_travel_alert(message_text):
    MAX_LINES_PER_SCREEN = 3
    MAX_CHARS_PER_LINE = DISPLAY_WIDTH // CHAR_WIDTH  # Maximum number of characters per line
    
    alert_text = "Travel Alert"
    centre_x = (DISPLAY_WIDTH - len(alert_text) * CHAR_WIDTH) // 2  # Center the text

    words = message_text.split()
    screens = []
    screen = []
    line = ''

    oled1.fill(0)
    # Flash the alert text before displaying the message
    for _ in range(2):
        oled1.text(alert_text, centre_x, LINETWO_Y)
        oled1.show()
        time.sleep(0.5)
        oled1.fill(0)
        oled1.show()
        time.sleep(0.5)

    for word in words:
        if len(line) + len(word) + 1 > MAX_CHARS_PER_LINE:  # +1 for the space
            screen.append(line)
            line = ''

            if len(screen) == MAX_LINES_PER_SCREEN:
                screens.append(screen)
                screen = []

        line += ' ' + word if line else word  # Add space only if line is not empty

    # Add the last line and screen if they're not empty
    if line:
        screen.append(line)
    if screen:
        screens.append(screen)

    for screen in screens:
        oled1.fill(0)  # Clear the display

        for i, line in enumerate(screen):
            oled1.text(line, 0, i * LINE_HEIGHT)

        oled1.show()  # Update the display

        time.sleep(3)  # Wait 3 seconds without yielding to the event loop

async def scroll_text(text, y, speed=5): # Speed is 1-5, 1 being slowest
    # print(f"scroll_text() called with text: {text}")
    text_width = len(text) * CHAR_WIDTH
    wait_secs = 0.01 + (speed - 1) * (0.001 - 0.01) / (5 - 1)
    
    for x in range(DISPLAY_WIDTH, -(text_width+1), -1):
        clear_line(y)
        oled1.text(text, x, y)
        oled1.show()
        await asyncio.sleep(wait_secs)  # Delay between frames
    
    await asyncio.sleep(3)  # Pause after finished scrolling

async def run_periodically(func, wait_seconds):
    await asyncio.sleep(wait_seconds)
    while True:
        await func()
        await asyncio.sleep(wait_seconds)

def format_calling_points(departure):
    calling_points = departure['subsequentCallingPoints']
    if not calling_points:
        return "Calling at destination only"
    
    # Format all but the last calling point
    calling_points_text = "Calling at: " + ', '.join(
        f"{calling_point['locationName']} ({calling_point['time_due']})"
        for calling_point in calling_points[:-1]
    )
    
    # Add 'and' before the last calling point
    last_calling_point = f"{calling_points[-1]['locationName']} ({calling_points[-1]['time_due']})"

    if calling_points_text:
        calling_points_text += f" and {last_calling_point}"
    else:
        calling_points_text = f"Calling at: {last_calling_point}"
    
    return calling_points_text

async def main():
    # print("main() called")
    rail_data_instance = rail_data.RailData()
  
    # At startup, run both functions once and wait
    await datetime_utils.sync_rtc()
    await rail_data_instance.get_rail_data()

    # Set them to run in the background from now on
    asyncio.create_task(run_periodically(datetime_utils.sync_rtc, urandom.randint(60, 6000)))  # TODO: Make just do the DST check not the clock sync
    asyncio.create_task(run_periodically(rail_data_instance.get_rail_data, urandom.randint(59, 119)))  # Run every 1-2 minutes

    clear_display()

    clock_task = asyncio.create_task(display_clock())

    while True:
        # If there's a first departure, show it
        if len(rail_data_instance.departures_list) > 0:
            clear_line(LINEONE_Y)
            oled1.text("1 " + rail_data_instance.departures_list[0]["destination"], 0, LINEONE_Y)
            oled1.fill_rect(85, LINEONE_Y, DISPLAY_WIDTH, LINE_HEIGHT, 0)
            oled1.text(rail_data_instance.departures_list[0]["time_due"], 88, LINEONE_Y)
            oled1.show()
            # print(format_calling_points(rail_data_instance.departures_list[0]))
            await scroll_text(format_calling_points(rail_data_instance.departures_list[0]), LINETWO_Y)
            await asyncio.sleep(1)
        else:
            clear_line(LINEONE_Y)
            oled1.text("No departures", 0, LINEONE_Y)
            oled1.show()
            await asyncio.sleep(12)

        # If there's a second departure, show it - after calling points have scrolled on line two
        if len(rail_data_instance.departures_list) > 1:
            clear_line(LINETWO_Y)
            oled1.text(rail_data_instance.departures_list[1]["destination"], 0, LINETWO_Y)
            oled1.fill_rect(85, LINETWO_Y, DISPLAY_WIDTH, LINE_HEIGHT, 0)
            oled1.text(rail_data_instance.departures_list[1]["time_due"], 88, LINETWO_Y)
            oled1.show()
            await asyncio.sleep(4)

        if rail_data_instance.nrcc_message:
            print("Displaying travel alert:", rail_data_instance.nrcc_message, "\n")
            clock_task.cancel()
            await display_travel_alert(rail_data_instance.nrcc_message)
            clock_task = asyncio.create_task(display_clock())
        else:
            await asyncio.sleep(3)

if __name__ == "__main__":
    setup_display()
    utils.connect_wifi()

    asyncio.run(main())