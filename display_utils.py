"""
Author: Adam Knowles
Version: 0.1
Name: display_utils.py
Description: Display utils for the Pico departure boards

GitHub Repository: https://github.com/Pharkie/picow-railway-departure
License: GNU General Public License (GPL)
"""

import asyncio
import utime
from micropython import const
import config

# from utils_logger import log_message


async def display_init_message_1screen(oled, screen_number, total_screens):
    """
    Displays an initialization message on a single screen of the OLED display.

    Parameters:
    oled (OLED): The OLED display object.
    screen_number (int): The current screen number.
    total_screens (int): The total number of screens.

    Side Effects:
    Updates the OLED display with the initialization message.
    """
    async with oled.oled_lock:
        oled.fill(0)
        oled.fd_oled.print_str("Loading", 0, config.LINEONE_Y)
        oled.fd_oled.print_str("Pico departures", 0, config.THIN_LINETWO_Y)
        oled.fd_oled.print_str(
            f"Screen {screen_number} of {total_screens}",
            0,
            config.THIN_LINETHREE_Y,
        )
        oled.show()


async def display_init_message(oled1, oled2):
    """
    Displays an initialization message on one or two OLED displays.

    Parameters:
    oled1 (OLED): The first OLED display object.
    oled2 (OLED): The second OLED display object, if available.

    Raises:
    RuntimeError: If oled1 is not available.

    Side Effects:
    Updates the OLED displays with the initialization message.
    """
    if not oled1:
        raise RuntimeError("oled1 not available")

    total_screens = 1 if not oled2 else 2

    for screen_number, oled in enumerate((oled1, oled2), start=1):
        if oled:
            await display_init_message_1screen(
                oled, screen_number, total_screens
            )


async def display_departure_line(
    oled, departure_number, destination, time_scheduled, y_pos
):
    """
    Asynchronously displays a departure line on the OLED display.

    Parameters:
    oled (OLED): The OLED display object.
    departure_number (str): The departure number to display.
    destination (str): The destination to display.
    time_scheduled (str): The scheduled time to display.
    y_pos (int): The y position on the display to start at.

    Side Effects:
    Updates the OLED display with the departure line.
    """
    # log_message(f"display_departure_line() showing train to {destination}", level="DEBUG")
    _max_length = const(12)

    # Split the destination into lines of up to max_length characters each, breaking
    # at word boundaries
    lines = wrap_text(destination, _max_length)

    while True:
        # Don't do exception handling here, let it bubble up to the main loop
        for line in lines:
            await clear_line(oled, y_pos)

            async with oled.oled_lock:
                oled.fd_oled.print_str(departure_number + line, 0, y_pos)
                oled.fill_rect(
                    97, y_pos, config.DISPLAY_WIDTH, config.THIN_LINE_HEIGHT, 0
                )  # Make room for time
                oled.fd_oled.print_str(time_scheduled, 99, y_pos)
                oled.show()
            await asyncio.sleep(3)


async def display_first_departure(
    oled, first_departure, rail_data_instance, screen_number
):
    """
    Asynchronously displays the first departure on the OLED display.

    Parameters:
    oled (OLED): The OLED display object.
    rail_data_instance (RailDataInstance): The rail data instance.
    screen_number (int): The screen number.

    Side Effects:
    Updates the OLED display with the first departure data.
    """
    first_departure_task = None

    if screen_number == 1:
        first_departure_task = rail_data_instance.oled1_first_departure_task
    elif screen_number == 2:
        first_departure_task = rail_data_instance.oled2_first_departure_task

    # If a display_first_departure_task is already running, cancel it
    if first_departure_task:
        first_departure_task.cancel()
        try:
            await first_departure_task
        except asyncio.CancelledError:
            pass

    if first_departure:
        new_task = asyncio.create_task(
            display_departure_line(
                oled,
                "1 ",
                first_departure["destination"],
                first_departure["time_scheduled"],
                config.LINEONE_Y,
            )
        )

        if screen_number == 1:
            rail_data_instance.oled1_first_departure_task = new_task
        elif screen_number == 2:
            rail_data_instance.oled2_first_departure_task = new_task

        await asyncio.sleep(3)

        time_estimated = first_departure["time_estimated"]

        await clear_line(oled, config.THICK_LINETWO_Y)

        # Second line: show "on time" or estimated time
        if time_estimated == "On time":
            await display_centred_text(
                oled, "Due on time", config.THICK_LINETWO_Y
            )
        else:
            await display_centred_text(
                oled, f"Now due: {time_estimated}", config.THICK_LINETWO_Y
            )

        await asyncio.sleep(3)
        await clear_line(oled, config.THIN_LINETWO_Y)
        await asyncio.sleep(2)

        # Second line: scroll the calling points
        await scroll_text(
            oled, format_calling_points(first_departure), config.THICK_LINETWO_Y
        )
        await asyncio.sleep(3)

        if screen_number == 1 and rail_data_instance.oled1_first_departure_task:
            rail_data_instance.oled1_first_departure_task.cancel()
        elif (
            screen_number == 2 and rail_data_instance.oled2_first_departure_task
        ):
            rail_data_instance.oled2_first_departure_task.cancel()


async def display_second_departure(oled, second_departure):
    """
    This coroutine displays the second departure on the OLED screen.

    Parameters:
    oled: The OLED display object.
    departures: A list of departures to display.
    """
    # print(f"Displaying second departure: {second_departure}")
    await clear_line(oled, config.THIN_LINETWO_Y)

    display_departure_task = asyncio.create_task(
        display_departure_line(
            oled,
            "2 ",
            second_departure["destination"],
            second_departure["time_scheduled"],
            config.THIN_LINETWO_Y,
        )
    )

    await asyncio.sleep(6)

    if display_departure_task:
        display_departure_task.cancel()


async def display_no_departures(oled):
    """
    This coroutine displays a "No departures" message on the OLED screen.

    Parameters:
    oled: The OLED display object.
    """
    await clear_line(oled, config.LINEONE_Y)
    await clear_line(oled, config.THIN_LINETWO_Y)
    line1_message = "No departures"

    async with oled.oled_lock:
        oled.fd_oled.print_str(
            line1_message,
            centre_x(line1_message, config.THIN_CHAR_WIDTH),
            config.LINEONE_Y,
        )

        line2_message = "in next 2 hours"
        oled.fd_oled.print_str(
            line2_message,
            centre_x(line2_message, config.THIN_CHAR_WIDTH),
            config.THIN_LINETWO_Y,
        )
        oled.show()

    await asyncio.sleep(12)


async def both_screen_text(
    oled1,
    oled2,
    text1,
    y1,
    text2=None,
    y2=None,
    text3=None,
    y3=None,
):
    """
    Displays up to three lines of text on both OLED displays.

    Parameters:
    oled1, oled2 (OLED): The OLED display objects.
    text1, text2, text3 (str): The text lines to display. If None, the line is not displayed.
    y1, y2, y3 (int): The y positions on the display to start each line at.

    Effect:
    Updates both OLED displays with the provided text lines.
    """
    for oled in (oled1, oled2):
        if oled is not None:
            async with oled.oled_lock:
                oled.fill(0)
                oled.fd_oled.print_str(text1, 0, y1)
                if text2 is not None and y2 is not None:
                    oled.fd_oled.print_str(text2, 0, y2)
                if text3 is not None and y3 is not None:
                    oled.fd_oled.print_str(text3, 0, y3)
                oled.show()


def format_calling_points(departure):
    """
    Formats the calling points of a departure into a string.

    Parameters:
    departure (dict): The departure data, including 'subsequentCallingPoints' and 'operator'.

    Returns:
    str: A string describing the calling points and the operator of the departure.
    """
    calling_points = departure["subsequentCallingPoints"]

    if not calling_points:
        return f"Calling at destination only. Operator: {departure['operator']}"

    # Format all but the last calling point
    calling_points_text = "Calling at: " + ", ".join(
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


async def display_centred_text(oled, text, y):
    """
    This function displays a given text centered on the OLED display at a given y-coordinate.

    Parameters:
    oled: The OLED display object.
    text: The text string to display.
    y: The y-coordinate at which to display the text.
    """
    text_width = len(text) * config.THICK_CHAR_WIDTH  # 8 pixels per character
    x = max(
        0, (config.DISPLAY_WIDTH - text_width) // 2
    )  # Calculate x-coordinate to center text

    async with oled.oled_lock:
        oled.fill_rect(0, y, config.DISPLAY_WIDTH, 8, 0)  # Clear the line
        oled.text(text, x, y)  # Display the text
        oled.show()


def centre_x(text, char_width):
    """
    Calculates the x-coordinate to centre a text message on the display.

    Parameters:
    text (str): The text message to be displayed.
    char_width (int): The width of a character on the display.

    Returns:
    int: The x-coordinate to start the text at to centre it on the display.
    """
    message_width = len(text) * char_width
    x = (config.DISPLAY_WIDTH - message_width) // 2
    # print(f"centre_x() called with text: {text}, char_width: {char_width}" +
    # f" message_width: {message_width}, x: {x}")
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
    words = text.split(" ")
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) <= max_length or not current_line:
            current_line += " " + word
        else:
            lines.append(current_line.strip())
            current_line = word

    lines.append(current_line.strip())
    return lines


async def clear_display(oled):
    """
    This function clears the OLED display.

    Parameters:
    oled: The OLED display object.
    """
    async with oled.oled_lock:
        oled.fill(0)
        oled.show()


async def clear_line(oled, y):
    """
    This function clears a specific line on the OLED display.

    Parameters:
    oled: The OLED display object.
    y: The y-coordinate of the line to clear.
    """
    async with oled.oled_lock:
        oled.fill_rect(0, y, config.DISPLAY_WIDTH, config.THICK_LINE_HEIGHT, 0)


async def display_clock(oled):
    """
    This coroutine displays the current time on an OLED screen.

    Parameters:
    oled: The OLED display object.
    """
    time_format = "{:02d}:{:02d}:{:02d}"
    offline_string = "[offline]"

    # Don't do Exception handling here, let it bubble up to the main loop
    while True:
        current_time = utime.localtime()
        current_seconds = utime.time()

        # async with oled.oled_lock:
        # Clear where the time is displayed without clearing whole line to save time (?)
        oled.fill_rect(
            40, config.THIN_LINETHREE_Y, 80, config.THIN_LINE_HEIGHT, 0
        )

        # offline_string_turn is true for 2 seconds every 15 seconds
        offline_string_turn = config.OFFLINE_MODE and current_seconds % 15 < 2

        if offline_string_turn:
            oled.fd_oled.print_str(offline_string, 40, config.THIN_LINETHREE_Y)
        else:
            clock_string = time_format.format(
                current_time[3], current_time[4], current_time[5]
            )
            # log_message(f"display_clock() updating {oled}", level="DEBUG")
            oled.fd_oled.print_str(clock_string, 46, config.THIN_LINETHREE_Y)

        oled.show()

        await asyncio.sleep(0.9)


async def display_travel_alert(oled, alert_message):
    """
    This coroutine displays a travel alert message on the OLED screen.

    Parameters:
    oled: The OLED display object.
    nrcc_message: A travel alert message to display.
    """
    max_lines_per_screen = 2  # Maximum number of lines per screen
    max_chars_per_line = 18  # Maximum number of characters per line

    preroll_text = "Travel Alert"
    preroll_centre_x = (
        config.DISPLAY_WIDTH - len(preroll_text) * config.THIN_CHAR_WIDTH
    ) // 2  # Center the text

    await clear_line(oled, config.LINEONE_Y)
    await clear_line(oled, config.THIN_LINETWO_Y)
    # Flash the alert text before displaying the message
    for _ in range(2):
        async with oled.oled_lock:
            oled.fd_oled.print_str(
                preroll_text, preroll_centre_x, config.LINEONE_Y
            )
            oled.show()
        await asyncio.sleep(0.5)
        await clear_line(oled, config.LINEONE_Y)
        async with oled.oled_lock:
            oled.show()
        await asyncio.sleep(0.5)

    words = alert_message.split()
    screens = []
    screen = []
    line = ""

    for word in words:
        if len(line) + len(word) + 1 > max_chars_per_line:  # +1 for the space
            screen.append(line)
            line = ""

            if len(screen) == max_lines_per_screen:
                screens.append(screen)
                screen = []

        line += (
            " " + word if line else word
        )  # Add space only if line is not empty

    # Add the last line and screen if they're not empty
    if line:
        screen.append(line)
    if screen:
        screens.append(screen)

    for screen in screens:
        await clear_line(oled, config.LINEONE_Y)
        await clear_line(oled, config.THIN_LINETWO_Y)

        for i, line in enumerate(screen):
            async with oled.oled_lock:
                oled.fd_oled.print_str(line, 0, i * config.THIN_LINE_HEIGHT)

        async with oled.oled_lock:
            oled.show()  # Update the display

        await asyncio.sleep(
            3
        )  # Wait 3 seconds without yielding to the event loop

    oled.fill(0)


async def scroll_text(oled, text, y):
    """
    Asynchronously scrolls a line of text across the OLED display.

    Parameters:
    oled (OLED): The OLED display object.
    text (str): The text to scroll.
    y (int): The y position on the display to start at.

    Side Effects:
    Updates the OLED display with the scrolling text.
    """
    # print(f"scroll_text() called with text: {text}")
    text_width = len(text) * config.THICK_CHAR_WIDTH
    frame_delay = 0.1  # Delay between frames
    step_size = 6  # Smoother scrolling takes too much CPU?

    for x in range(config.DISPLAY_WIDTH, -(text_width + step_size), -step_size):
        await clear_line(oled, y)
        async with oled.oled_lock:
            oled.text(text, x, y)
            oled.show()

        await asyncio.sleep(frame_delay)  # Delay between frames
