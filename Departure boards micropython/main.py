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
import framebuf
from lib.fdrawer import FontDrawer
from config import LINEONE_Y, THIN_LINETWO_Y, THIN_LINETHREE_Y, THIN_LINE_HEIGHT, THICK_LINE_HEIGHT, THICK_LINETWO_Y, THICK_LINETHREE_Y, THICK_CHAR_WIDTH
from config import DISPLAY_WIDTH, DISPLAY_HEIGHT, THIN_CHAR_WIDTH, offline_mode

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
        oled.text("Pico departures", 0, THIN_LINETWO_Y)
        oled.show()

        return oled
    except Exception as e:
        print(f"Failed to initialize {display_name}. Error: {str(e)}")
        return None

def setup_displays():
    i2c_oled1 = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)
    i2c_oled2 = I2C(1, scl=Pin(19), sda=Pin(18), freq=200000)

    oled1 = initialize_oled(i2c_oled1, "oled1")
    oled2 = initialize_oled(i2c_oled2, "oled2")

    if oled2 is None:
        print("No oled2. Skipping operations on second screen.")

    return oled1, oled2

def clear_display(oled):
    oled.fill(0)
    oled.show()

def clear_line(oled, y):
    oled.fill_rect(0, y, DISPLAY_WIDTH, THICK_LINE_HEIGHT, 0)

async def display_clock(oled, fd_oled):
    time_string = "{:02d}:{:02d}:{:02d}"
    text_width = len(time_string.format(0, 0, 0)) * THIN_CHAR_WIDTH  # 8 pixels per character
    clock_centre_x = (DISPLAY_WIDTH - text_width) // 2

    offline_string = "[offline]"
    offline_width = len(offline_string) * THIN_CHAR_WIDTH
    offline_centre_x = (DISPLAY_WIDTH - offline_width) // 2

    counter = 0
    while True:
        current_time = utime.localtime()
        # Clear where the time is displayed
        oled.fill_rect(offline_centre_x, THIN_LINETHREE_Y, offline_width, THIN_LINE_HEIGHT, 0)

        if offline_mode and counter <= 2:
            fd_oled.print_str(offline_string, offline_centre_x, THIN_LINETHREE_Y)
        else:
            fd_oled.print_str(time_string.format(current_time[3], current_time[4], current_time[5]), clock_centre_x, THIN_LINETHREE_Y)

        if offline_mode:
            counter += 1
            if counter == 15:
                counter = 0

        oled.show()  
        await asyncio.sleep(0.9)  # Setting to 0.9 helps clock not skip seconds when device busy

async def display_travel_alert(oled, rail_data_instance):
    print("Displaying travel alert:", rail_data_instance.nrcc_message, "\n")

    message_text = rail_data_instance.nrcc_message

    MAX_LINES_PER_SCREEN = 3
    MAX_CHARS_PER_LINE = DISPLAY_WIDTH // THIN_CHAR_WIDTH  # Maximum number of characters per line
    
    alert_text = "Travel Alert"
    centre_x = (DISPLAY_WIDTH - len(alert_text) * THIN_CHAR_WIDTH) // 2  # Center the text

    words = message_text.split()
    screens = []
    screen = []
    line = ''

    oled.fill(0)
    # Flash the alert text before displaying the message
    for _ in range(2):
        oled.text(alert_text, centre_x, THIN_LINETWO_Y)
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
            oled.text(line, 0, i * THIN_LINE_HEIGHT)

        oled.show()  # Update the display

        time.sleep(3)  # Wait 3 seconds without yielding to the event loop

async def scroll_text(oled, text, y):
    # print(f"scroll_text() called with text: {text}")
    text_width = len(text) * THICK_CHAR_WIDTH
    frame_delay = 0.1 # Going under this causes problems
    step_size = 6 # Smoother scrolling takes too much CPU

    for x in range(DISPLAY_WIDTH, -(text_width+step_size), -step_size): 
        clear_line(oled, y)
        oled.text(text, x, y)
        oled.show()

        await asyncio.sleep(frame_delay)  # Delay between frames

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
    text_width = len(text) * THICK_CHAR_WIDTH  # 8 pixels per character
    x = max(0, (DISPLAY_WIDTH - text_width) // 2)  # Calculate x-coordinate to center text
    oled.fill_rect(0, y, DISPLAY_WIDTH, 8, 0)  # Clear the line
    oled.text(text, x, y)  # Display the text
    oled.show()

def wrap_text(text, max_length):
    words = text.split(' ')
    lines = []
    current_line = ''

    for word in words:
        if len(current_line) + len(word) <= max_length or not current_line:
            current_line += ' ' + word
        else:
            lines.append(current_line.strip())
            current_line = word

    lines.append(current_line.strip())
    return lines

async def display_first_departure_line_one(oled, fd_oled, destination, time_scheduled):
    max_length = 12

    # Split the destination into lines of up to max_length characters each, breaking at word boundaries
    lines = wrap_text(destination, max_length)

    while True:
        for line in lines:
            clear_line(oled, LINEONE_Y)

            fd_oled.print_str("1 " + line, 0, LINEONE_Y)

            # oled.text("1 " + line, 0, LINEONE_Y)
            oled.fill_rect(97, LINEONE_Y, DISPLAY_WIDTH, THIN_LINE_HEIGHT, 0) # Make room for time
            fd_oled.print_str(time_scheduled, 99, LINEONE_Y)
            # oled.text(time_scheduled, 88, LINEONE_Y)
            oled.show()
            await asyncio.sleep(3)
    
async def display_first_departure(oled, fd_oled, departures):
    # print(f"Displaying first departure for: {oled} = {departures}")

    line_one_task = asyncio.create_task(display_first_departure_line_one(oled, fd_oled, departures[0]["destination"], departures[0]["time_scheduled"]))
    await asyncio.sleep(3)

    time_estimated = departures[0]["time_estimated"]

    clear_line(oled, THICK_LINETWO_Y)

    # Second line: show "on time" or estimated time
    if time_estimated == "On time":
        display_centred_text(oled, "Due on time", THICK_LINETWO_Y)
    else:
        display_centred_text(oled, f"Now due: {time_estimated}", THICK_LINETWO_Y)

    await asyncio.sleep(3)
    clear_line(oled, THIN_LINETWO_Y)
    await asyncio.sleep(2)

    # Second line: scroll the calling points
    await scroll_text(oled, format_calling_points(departures[0]), THIN_LINETWO_Y)
    await asyncio.sleep(3)
    
    if line_one_task:
        line_one_task.cancel()

async def display_second_departure(oled, fd_oled, departures):
    clear_line(oled, THIN_LINETWO_Y)
    # oled.text("2 " + departures[1]["destination"], 0, LINETWO_Y)
    fd_oled.print_str("2 " + departures[1]["destination"], 0, THIN_LINETWO_Y)
    oled.fill_rect(97, THIN_LINETWO_Y, DISPLAY_WIDTH, THIN_LINE_HEIGHT, 0)
    # oled.text(departures[1]["time_scheduled"], 88, LINETWO_Y)
    fd_oled.print_str(departures[1]["time_scheduled"], 99, THIN_LINETWO_Y)
    oled.show()
    await asyncio.sleep(4)

async def display_no_departures(oled, fd_oled):
    clear_line(oled, LINEONE_Y)
    clear_line(oled, THIN_LINETWO_Y)
    fd_oled.print_str("No departures", 0, LINEONE_Y)
    # oled.text("No departures", 0, LINEONE_Y)
    oled.show()
    await asyncio.sleep(12)

async def run_oled(oled, fd_oled, departures, nrcc_message, clock_task):
    # Show first departure for each screen on line one, and scroll the calling points on line two
    if len(departures) > 0:
        await display_first_departure(oled, fd_oled, departures)
    else:
        await display_no_departures(oled, fd_oled)

    # If there is a second departure for this screen, show it on line two
    if len(departures) > 1:
        await display_second_departure(oled, fd_oled, departures)

    if nrcc_message:
        clock_task.cancel()
        await display_travel_alert(oled, fd_oled, nrcc_message)
        clock_task = asyncio.create_task(display_clock(fd_oled))
    else:
        await asyncio.sleep(3)

async def main(oled1, oled2):
    # print("main() called")
    rail_data_instance = rail_data.RailData()
  
    # At startup, run both functions once and wait
    await datetime_utils.sync_rtc()
    await rail_data_instance.get_rail_data()

    # Set them to run in the background from now on
    if not offline_mode:
        asyncio.create_task(run_periodically(datetime_utils.sync_rtc, urandom.randint(60, 6000)))  # TODO: Make just do the DST check not the clock sync
        asyncio.create_task(run_periodically(rail_data_instance.get_rail_data, urandom.randint(59, 119)))  # Run every 1-2 minutes

    clear_display(oled1)
    clear_display(oled2)

    fd_oled1 = FontDrawer(frame_buffer=oled1, font_name = 'dejav_m10')
    fd_oled2 = FontDrawer(frame_buffer=oled2, font_name = 'dejav_m10')

    oled1_clock_task = asyncio.create_task(display_clock(oled1, fd_oled1))
    oled2_clock_task = asyncio.create_task(display_clock(oled2, fd_oled2))

    oled1_task, oled2_task = None, None
    
    while True:
        if not oled1_task or oled1_task.done():
            oled1_task = asyncio.create_task(run_oled(oled1, fd_oled1, rail_data_instance.oled1_departures, rail_data_instance.nrcc_message, oled1_clock_task))
        if oled2 and (not oled2_task or oled2_task.done()):
            oled2_task = asyncio.create_task(run_oled(oled2, fd_oled2, rail_data_instance.oled2_departures, rail_data_instance.nrcc_message, oled2_clock_task))
        await asyncio.sleep(1) # Without this, nothing has time to run

def both_screen_text(oled1, oled2, text1, y1, text2=None, y2=None, text3=None, y3=None):
    for oled in (oled1, oled2):
        if oled is not None:
            oled.fill(0)
            oled.text(text1, 0, y1)
            if text2 is not None and y2 is not None:
                oled.text(text2, 0, y2)
            if text3 is not None and y3 is not None:
                oled.text(text3, 0, y3)
            oled.show()

if __name__ == "__main__":
    oled1, oled2 = setup_displays()

    if not offline_mode:
        utils.connect_wifi(oled1)

    asyncio.run(main(oled1, oled2))