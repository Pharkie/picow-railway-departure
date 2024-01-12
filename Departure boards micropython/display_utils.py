"""
Author: Adam Knowles
Version: 0.1
Name: display_utils.py
Description: Display utils for the Pico departure boards

GitHub Repository: https://github.com/Pharkie/picow-railway-departure
Based on work by Stewart Watkiss - PenguinTutor
License: GNU General Public License (GPL)
"""
from machine import Pin, I2C
import utime
import uasyncio as asyncio
import time
from config import LINEONE_Y, THIN_LINETWO_Y, THIN_LINETHREE_Y, THIN_LINE_HEIGHT, THICK_LINE_HEIGHT, THICK_LINETWO_Y, THICK_LINETHREE_Y, THICK_CHAR_WIDTH
from config import DISPLAY_WIDTH, DISPLAY_HEIGHT, THIN_CHAR_WIDTH, offline_mode

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

async def display_travel_alert(oled, fd_oled, nrcc_message):
    MAX_LINES_PER_SCREEN = 3
    MAX_CHARS_PER_LINE = DISPLAY_WIDTH // THIN_CHAR_WIDTH  # Maximum number of characters per line
    
    alert_text = "Travel Alert"
    centre_x = (DISPLAY_WIDTH - len(alert_text) * THIN_CHAR_WIDTH) // 2  # Center the text

    words = nrcc_message.split()
    screens = []
    screen = []
    line = ''

    oled.fill(0)
    # Flash the alert text before displaying the message
    for _ in range(2):
        fd_oled.print_str(alert_text, centre_x, THIN_LINETWO_Y)
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
            fd_oled.print_str(line, 0, i * THIN_LINE_HEIGHT)

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