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
from config import LINEONE_Y, LINETWO_Y, LINETHREE_Y, DISPLAY_WIDTH, DISPLAY_HEIGHT, LINE_HEIGHT, CHAR_WIDTH, offline_mode
from my_global_vars import oled1, oled2

def initialize_oled(i2c, display_name):
    try:
        devices = i2c.scan()
        if devices:
            print(f"I2C found for {display_name}: {hex(i2c.scan()[0]).upper()}. Config: {str(i2c)}")
        else:
            print(f"No I2C devices found on {display_name}.")

        oled = SSD1306_I2C(DISPLAY_WIDTH, DISPLAY_HEIGHT, i2c)
        oled.fill(0)
        oled.text("Loading", 0, LINEONE_Y)
        oled.text("Pico departures", 0, LINETWO_Y)
        oled.show()

        return oled
    except Exception as e:
        print(f"Failed to initialize {display_name}. Error: {str(e)}")
        return None

def setup_displays():
    global oled1, oled2

    i2c_oled1 = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)
    i2c_oled2 = I2C(1, scl=Pin(19), sda=Pin(18), freq=200000)

    oled1 = initialize_oled(i2c_oled1, "oled1")
    oled2 = initialize_oled(i2c_oled2, "oled2")

    if oled2 is None:
        print("No oled2. Skipping operations on second screen.")

def clear_display(oled):
    oled.fill(0)
    oled.show()

def clear_line(oled, y):
    oled.fill_rect(0, y, DISPLAY_WIDTH, LINE_HEIGHT, 0)

async def display_clock(oled):
    time_string = "{:02d}:{:02d}:{:02d}"
    text_width = len(time_string.format(0, 0, 0)) * 8  # 8 pixels per character
    centre_x = (DISPLAY_WIDTH - text_width) // 2

    while True:
        current_time = utime.localtime()
        # Clear where the time is displayed
        oled.fill_rect(centre_x, LINETHREE_Y, text_width, 8, 0)
        oled.text(time_string.format(current_time[3], current_time[4], current_time[5]), centre_x, LINETHREE_Y)
        oled.show()  
        await asyncio.sleep(1)  # Update every second

async def display_travel_alert(oled, rail_data_instance, clock_task):
    print("Displaying travel alert:", rail_data_instance.nrcc_message, "\n")

    message_text = rail_data_instance.nrcc_message

    MAX_LINES_PER_SCREEN = 3
    MAX_CHARS_PER_LINE = DISPLAY_WIDTH // CHAR_WIDTH  # Maximum number of characters per line
    
    clock_task.cancel()

    alert_text = "Travel Alert"
    centre_x = (DISPLAY_WIDTH - len(alert_text) * CHAR_WIDTH) // 2  # Center the text

    words = message_text.split()
    screens = []
    screen = []
    line = ''

    oled.fill(0)
    # Flash the alert text before displaying the message
    for _ in range(2):
        oled.text(alert_text, centre_x, LINETWO_Y)
        oled.show()
        time.sleep(0.5)
        oled.fill(0)
        oled.show()
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
        oled.fill(0)  # Clear the display

        for i, line in enumerate(screen):
            oled.text(line, 0, i * LINE_HEIGHT)

        oled.show()  # Update the display

        time.sleep(3)  # Wait 3 seconds without yielding to the event loop
    
    clock_task = asyncio.create_task(display_clock(oled))

"""
This function combines the clock to save resources and task switching to help the scroll be smooth.
"""
async def scroll_text_with_clock(oled, text, y, speed=5): # Speed is 1-5, 1 being slowest
    # print(f"scroll_text() called with text: {text}")
    text_width = len(text) * CHAR_WIDTH
    wait_secs = 0.02 + (speed - 1) * (0.005 - 0.02) / (5 - 1)

    time_string = "{:02d}:{:02d}:{:02d}"
    clock_text_width = len(time_string.format(0, 0, 0)) * 8  # 8 pixels per character

    clock_centre_x = (DISPLAY_WIDTH - clock_text_width) // 2
    last_time = None
    
    for x in range(DISPLAY_WIDTH, -(text_width+1), -2):
        clear_line(oled, y)
        oled.text(text, x, y)

        current_time = utime.localtime()
        if last_time != current_time: # Only update the display if the time has changed
            # Clear only the area where the time is displayed
            oled.fill_rect(clock_centre_x, LINETHREE_Y, clock_text_width, 8, 0)
            oled.text(time_string.format(current_time[3], current_time[4], current_time[5]), clock_centre_x, LINETHREE_Y)

            # print(f"Displaying time {time_string.format(current_time[3], current_time[4], current_time[5]), centre_x}")

            last_time = current_time
        
        oled.show()

        await asyncio.sleep(wait_secs)  # Delay between frames

async def run_periodically(func, wait_seconds):
    await asyncio.sleep(wait_seconds)
    while True:
        await func()
        await asyncio.sleep(wait_seconds)

def format_calling_points(departure):
    calling_points = departure['subsequentCallingPoints']

    if not calling_points:
        return f"Calling at destination only. Operator: {departure['operator']}"
    
    # Format all but the last calling point
    calling_points_text = "Calling at: " + ', '.join(
        f"{calling_point['locationName']} {calling_point['time_due']}"
        for calling_point in calling_points[:-1]
    )
    
    # Add 'and' before the last calling point
    last_calling_point = f"{calling_points[-1]['locationName']} {calling_points[-1]['time_due']}"

    if calling_points_text:
        calling_points_text += f" and {last_calling_point}"
    else:
        calling_points_text = f"Calling at: {last_calling_point}"
    
    # Add operator at the end
    calling_points_text += f" ({departure['operator']})"
    
    return calling_points_text

def display_centred_text(oled, text, y):
    text_width = len(text) * CHAR_WIDTH  # 8 pixels per character
    x = max(0, (DISPLAY_WIDTH - text_width) // 2)  # Calculate x-coordinate to center text
    oled.fill_rect(0, y, DISPLAY_WIDTH, 8, 0)  # Clear the line
    oled.text(text, x, y)  # Display the text
    oled.show()

async def display_first_departure(oled, rail_data_instance, clock_task):
    departures = rail_data_instance.oled1_departures if oled == oled1 else rail_data_instance.oled2_departures

    # print(f"Displaying first departure for: {oled} = {departures}")

    clear_line(oled, LINEONE_Y)
    oled.text("1 " + departures[0]["destination"], 0, LINEONE_Y)
    oled.fill_rect(85, LINEONE_Y, DISPLAY_WIDTH, LINE_HEIGHT, 0)
    oled.text(departures[0]["time_scheduled"], 88, LINEONE_Y)
    oled.show()
    await asyncio.sleep(3)

    time_estimated = departures[0]["time_estimated"]

    if time_estimated == "On time":
        display_centred_text(oled, "Due on time", LINETWO_Y)
    else:
        display_centred_text(oled, f"Now due: {time_estimated}", LINETWO_Y)

    await asyncio.sleep(3)
    clear_line(oled, LINETWO_Y)
    await asyncio.sleep(2)

    clock_task.cancel() # Cancel the clock task so it doesn't interfere with the scrolling text
    await scroll_text_with_clock(oled, format_calling_points(departures[0]), LINETWO_Y)
    clock_task = asyncio.create_task(display_clock(oled))
    await asyncio.sleep(3)

async def display_no_departures(oled):
    clear_line(oled, LINEONE_Y)
    clear_line(oled, LINETWO_Y)
    oled.text("No departures", 0, LINEONE_Y)
    oled.show()
    await asyncio.sleep(12)

async def display_second_departure(oled, rail_data_instance):
    departures = rail_data_instance.oled1_departures if oled == oled1 else rail_data_instance.oled2_departures

    clear_line(oled, LINETWO_Y)
    oled.text("2 " + departures[1]["destination"], 0, LINETWO_Y)
    oled.fill_rect(85, LINETWO_Y, DISPLAY_WIDTH, LINE_HEIGHT, 0)
    oled.text(departures[1]["time_scheduled"], 88, LINETWO_Y)
    oled.show()
    await asyncio.sleep(4)

async def run_oled(oled, rail_data_instance, clock_task):
    while True:
        departures = rail_data_instance.oled1_departures if oled == oled1 else rail_data_instance.oled2_departures

        # Show first departure for each screen on line one, and scroll the calling points on line two
        if len(departures) > 0:
            await display_first_departure(oled, rail_data_instance, clock_task)
        else:
            await display_no_departures(oled)

        # If there is a second departure for this screen, show it on line two
        if len(departures) > 1:
            await display_second_departure(oled, rail_data_instance)

        if rail_data_instance.nrcc_message:
            await display_travel_alert(oled, rail_data_instance, clock_task)
        else:
            await asyncio.sleep(3)

async def main():
    # print("main() called")
    rail_data_instance = rail_data.RailData()
  
    # At startup, run both functions once and wait
    await datetime_utils.sync_rtc()
    await rail_data_instance.get_rail_data()

    # Set them to run in the background from now on
    asyncio.create_task(run_periodically(datetime_utils.sync_rtc, urandom.randint(60, 6000)))  # TODO: Make just do the DST check not the clock sync
    asyncio.create_task(run_periodically(rail_data_instance.get_rail_data, urandom.randint(59, 119)))  # Run every 1-2 minutes

    clear_display(oled1)
    clear_display(oled2)

    oled1_clock_task = asyncio.create_task(display_clock(oled1))
    oled2_clock_task = asyncio.create_task(display_clock(oled2))

    await asyncio.gather(
        run_oled(oled1, rail_data_instance, oled1_clock_task),
        run_oled(oled2, rail_data_instance, oled2_clock_task)
    )

if __name__ == "__main__":
    setup_displays()

    if offline_mode:
        time.sleep(1)
        oled1.fill(0)
        oled1.text("Config set for", 0, LINEONE_Y)
        oled1.text("offline mode", 0, LINETWO_Y)
        oled1.show()
        time.sleep(3)
    else:
        utils.connect_wifi(oled1)

    asyncio.run(main())