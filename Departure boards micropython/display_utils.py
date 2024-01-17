"""
Author: Adam Knowles
Version: 0.1
Name: display_utils.py
Description: Display utils for the Pico departure boards

GitHub Repository: https://github.com/Pharkie/picow-railway-departure
Based on work by Stewart Watkiss - PenguinTutor
License: GNU General Public License (GPL)
"""
import utime
import uasyncio as asyncio
from micropython import const
import config

def display_init_message(oled1, oled2, fd_oled1, fd_oled2):
    screens = [(oled1, fd_oled1, 1), (oled2, fd_oled2, 2)]
    number_of_screens = 2 if oled2 is not None else 1

    for oled, fd_oled, screen_number in screens:
        if oled is not None:
            oled.fill(0)
            fd_oled.print_str("Loading", 0, config.LINEONE_Y)
            fd_oled.print_str("Pico departures", 0, config.THIN_LINETWO_Y)
            fd_oled.print_str(f"Screen {screen_number} of {number_of_screens}", 0, config.THIN_LINETHREE_Y)
            oled.show()

async def display_departure_line(oled, fd_oled, departure_number, destination, time_scheduled, y_pos):
    _max_length = const(12)

    # Split the destination into lines of up to max_length characters each, breaking at word boundaries
    lines = wrap_text(destination, _max_length)

    while True:
        for line in lines:
            clear_line(oled, y_pos)

            fd_oled.print_str(departure_number + line, 0, y_pos)
            oled.fill_rect(97, y_pos, config.DISPLAY_WIDTH, config.THIN_LINE_HEIGHT, 0) # Make room for time
            fd_oled.print_str(time_scheduled, 99, y_pos)
            oled.show()
            await asyncio.sleep(3)

async def display_first_departure(oled, fd_oled, first_departure):
    # print(f"Displaying first departure for: {oled} = {departures}")

    display_departure_task = asyncio.create_task(
        display_departure_line(
            oled,
            fd_oled,
            "1 ",
            first_departure["destination"], 
            first_departure["time_scheduled"],
            config.LINEONE_Y
        )
    )
    await asyncio.sleep(3)

    time_estimated = first_departure["time_estimated"]

    clear_line(oled, config.THICK_LINETWO_Y)

    # Second line: show "on time" or estimated time
    if time_estimated == "On time":
        display_centred_text(oled, "Due on time", config.THICK_LINETWO_Y)
    else:
        display_centred_text(oled, f"Now due: {time_estimated}", config.THICK_LINETWO_Y)

    await asyncio.sleep(3)
    clear_line(oled, config.THIN_LINETWO_Y)
    await asyncio.sleep(2)

    # Second line: scroll the calling points
    await scroll_text(oled, format_calling_points(first_departure), config.THIN_LINETWO_Y)
    await asyncio.sleep(3)
    
    if display_departure_task:
        display_departure_task.cancel()

async def display_second_departure(oled, fd_oled, second_departure):
    """
    This coroutine displays the second departure on the OLED screen.

    Parameters:
    oled: The OLED display object.
    fd_oled: The FontDrawer object for the OLED display.
    departures: A list of departures to display.
    """
    # print(f"Displaying second departure: {second_departure}")
    clear_line(oled, config.THIN_LINETWO_Y)

    display_departure_task = asyncio.create_task(
        display_departure_line(
            oled,
            fd_oled,
            "2 ",
            second_departure["destination"],
            second_departure["time_scheduled"],
            config.THIN_LINETWO_Y
        )
    )
    
    await asyncio.sleep(6)
    
    if display_departure_task:
        display_departure_task.cancel()

async def display_no_departures(oled, fd_oled):
    """
    This coroutine displays a "No departures" message on the OLED screen.

    Parameters:
    oled: The OLED display object.
    fd_oled: The FontDrawer object for the OLED display.
    """
    clear_line(oled, config.LINEONE_Y)
    clear_line(oled, config.THIN_LINETWO_Y)
    line1_message = "No departures"
    fd_oled.print_str(line1_message, centre_x(line1_message, config.THIN_CHAR_WIDTH), config.LINEONE_Y)

    line2_message = "in next 2 hours"
    fd_oled.print_str(line2_message, centre_x(line2_message, config.THIN_CHAR_WIDTH), config.THIN_LINETWO_Y)
    oled.show()
    await asyncio.sleep(12)

def both_screen_text(oled1, oled2, fd_oled1, fd_oled2, text1, y1, text2=None, y2=None, text3=None, y3=None):
    for i, oled in enumerate((oled1, oled2)):
        if oled is not None:
            oled.fill(0)
            if i == 0:  # oled1 is being processed
                fd_oled1.print_str(text1, 0, y1)
                if text2 is not None and y2 is not None:
                    fd_oled1.print_str(text2, 0, y2)
                if text3 is not None and y3 is not None:
                    fd_oled1.print_str(text3, 0, y3)
            else:  # oled2 is being processed
                fd_oled2.print_str(text1, 0, y1)
                if text2 is not None and y2 is not None:
                    fd_oled2.print_str(text2, 0, y2)
                if text3 is not None and y3 is not None:
                    fd_oled2.print_str(text3, 0, y3)
            oled.show()

def format_calling_points(departure):
    calling_points = departure['subsequentCallingPoints']

    if not calling_points:
        return f"Calling at destination only. Operator: {departure['operator']}"
    
    # Format all but the last calling point
    calling_points_text = "Calling at: " + ', '.join(
        f"{calling_point[0]} {calling_point[1]}"
        for calling_point in calling_points[:-1]
    )
    
    # Add 'and' before the last calling point
    last_calling_point = f"{calling_points[-1][0]} {calling_points[-1][1]}"

    if calling_points_text and len(calling_points) > 1:
        calling_points_text += f" and {last_calling_point}"
    else:
        calling_points_text = f"Calling at: {last_calling_point}"
    
    # Add operator at the end
    calling_points_text += f" ({departure['operator']})"
    
    return calling_points_text

def display_centred_text(oled, text, y):
    """
    This function displays a given text centered on the OLED display at a given y-coordinate.

    Parameters:
    oled: The OLED display object.
    text: The text string to display.
    y: The y-coordinate at which to display the text.
    """
    text_width = len(text) * config.THICK_CHAR_WIDTH  # 8 pixels per character
    x = max(0, (config.DISPLAY_WIDTH - text_width) // 2)  # Calculate x-coordinate to center text
    oled.fill_rect(0, y, config.DISPLAY_WIDTH, 8, 0)  # Clear the line
    oled.text(text, x, y)  # Display the text
    oled.show()

def centre_x(text, char_width):
    message_width = len(text) * char_width
    x = (config.DISPLAY_WIDTH - message_width) // 2
    # print(f"centre_x() called with text: {text}, char_width: {char_width}, message_width: {message_width}, x: {x}")
    return x

def wrap_text(text, max_length):
    """
    This function wraps a given text to a specified maximum length.

    Parameters:
    text: The text string to wrap.
    max_length: The maximum length of a line of text.

    Returns:
    lines: A list of lines of text, each line being no longer than max_length.
    """
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
    """
    This function clears the OLED display.

    Parameters:
    oled: The OLED display object.
    """
    oled.fill(0)
    oled.show()

def clear_line(oled, y):
    """
    This function clears a specific line on the OLED display.

    Parameters:
    oled: The OLED display object.
    y: The y-coordinate of the line to clear.
    """
    oled.fill_rect(0, y, config.DISPLAY_WIDTH, config.THICK_LINE_HEIGHT, 0)

async def display_clock(oled, fd_oled):
    """
    This coroutine displays the current time on an OLED screen.

    Parameters:
    oled: The OLED display object.
    fd_oled: The FontDrawer object for the OLED display.
    """
    time_format = "{:02d}:{:02d}:{:02d}"
    offline_string = "[offline]"

    counter = 0
    while True:
        current_time = utime.localtime()
        # Clear where the time is displayed without clearing whole line to save time (?)
        oled.fill_rect(40, config.THIN_LINETHREE_Y, 80, config.THIN_LINE_HEIGHT, 0)

        if config.offline_mode and counter <= 2:
            fd_oled.print_str(offline_string, 40, config.THIN_LINETHREE_Y)
        else:
            clock_string = time_format.format(current_time[3], current_time[4], current_time[5])
            fd_oled.print_str(clock_string, 46, config.THIN_LINETHREE_Y) # Hardcoded x to save calcs

        if config.offline_mode:
            counter += 1
            if counter == 15:
                counter = 0

        oled.show()  
        await asyncio.sleep(0.9)  # Setting to 0.9 helps clock not skip seconds when device busy

async def display_travel_alert(oled, fd_oled, alert_message):
    """
    This coroutine displays a travel alert message on the OLED screen.

    Parameters:
    oled: The OLED display object.
    fd_oled: The FontDrawer object for the OLED display.
    nrcc_message: A travel alert message to display.
    """
    MAX_LINES_PER_SCREEN = 2  # Maximum number of lines per screen
    MAX_CHARS_PER_LINE = 19  # Maximum number of characters per line
    
    preroll_text = "Travel Alert"
    preroll_centre_x = (config.DISPLAY_WIDTH - len(preroll_text) * config.THIN_CHAR_WIDTH) // 2  # Center the text

    clear_line(oled, config.LINEONE_Y)
    clear_line(oled, config.THIN_LINETWO_Y)
    # Flash the alert text before displaying the message
    for _ in range(2):
        fd_oled.print_str(preroll_text, preroll_centre_x, config.LINEONE_Y)
        
        oled.show()
        await asyncio.sleep(0.5)
        clear_line(oled, config.LINEONE_Y)
        oled.show()
        await asyncio.sleep(0.5)

    words = alert_message.split()
    screens = []
    screen = []
    line = ''

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
        clear_line(oled, config.LINEONE_Y)
        clear_line(oled, config.THIN_LINETWO_Y)

        for i, line in enumerate(screen):
            fd_oled.print_str(line, 0, i * config.THIN_LINE_HEIGHT)

        oled.show()  # Update the display

        await asyncio.sleep(3)  # Wait 3 seconds without yielding to the event loop
    
    oled.fill(0)

async def scroll_text(oled, text, y):
    # print(f"scroll_text() called with text: {text}")
    text_width = len(text) * config.THICK_CHAR_WIDTH
    FRAME_DELAY = 0.1 # Going under this causes problems
    STEP_SIZE = 6 # Smoother scrolling takes too much CPU

    for x in range(config.DISPLAY_WIDTH, -(text_width+STEP_SIZE), -STEP_SIZE): 
        clear_line(oled, y)
        oled.text(text, x, y)
        oled.show()

        await asyncio.sleep(FRAME_DELAY)  # Delay between frames