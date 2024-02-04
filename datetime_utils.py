"""
Author: Adam Knowles
Version: 0.1
Name: datetime_utils.py
Description: Utils that operate on datetime

GitHub Repository: https://github.com/Pharkie/AdamGalactic/
License: GNU General Public License (GPL)
"""

import random
import utime
import ntptime
import machine
import utils
from config import OFFLINE_MODE


def format_date(dt):
    # Format the date as 'DD MMM YYYY'.
    months = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    day = "{:02d}".format(dt[2])
    month = months[dt[1] - 1]
    year = "{:04d}".format(dt[0])
    return f"{day} {month} {year}"


def last_sunday(year, month):
    # Calculate the date of the last Sunday of the specified month and year.
    # Find the date of the last Sunday in a given month
    last_day = (
        utime.mktime((year, month + 1, 1, 0, 0, 0, 0, 0))
        - 86400  # pylint: disable=no-value-for-parameter
    )  # Set to the last day of the previous month
    weekday = utime.localtime(last_day)[6]  # Get the weekday for the last day

    while weekday != 6:  # Sunday has index 6
        last_day -= 86400  # Subtract a day in seconds
        weekday = (weekday - 1) % 7
    return int(last_day)


def is_DST(timestamp):
    # Check if the given timestamp is in DST (BST) considering the 1 am transition
    time_tuple = utime.localtime(timestamp)
    dst_start = last_sunday(time_tuple[0], 3)  # Last Sunday of March
    dst_end = last_sunday(time_tuple[0], 10)  # Last Sunday of October

    # Check if the current time is within DST dates
    if dst_start <= timestamp < dst_end:
        # Check if it's after 1 am on the last Sunday of March and before 2 am on the last Sunday of October
        if (
            time_tuple[1] == 3
            and time_tuple[2] == (dst_start // 86400) + 1
            and time_tuple[3] < 1
        ) or (
            time_tuple[1] == 10
            and time_tuple[2] == (dst_end // 86400)
            and time_tuple[3] < 2
        ):
            return False  # Not in DST during the 1 am transition
        else:
            return True  # In DST during other times
    else:
        return False


def get_time_values(current_time_tuple=None):
    # Split a time into individual digits, defaulting to current, real time.
    if current_time_tuple is None:
        current_time_tuple = utime.localtime()

    # Extract digits
    month_names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    day_of_month = current_time_tuple[2]
    month_name = month_names[current_time_tuple[1] - 1]
    year = current_time_tuple[0]
    hours_tens, hours_ones = divmod(current_time_tuple[3], 10)
    minutes_tens, minutes_ones = divmod(current_time_tuple[4], 10)
    seconds_tens, seconds_ones = divmod(current_time_tuple[5], 10)

    # Return the extracted digits
    return (
        hours_tens,
        hours_ones,
        minutes_tens,
        minutes_ones,
        seconds_tens,
        seconds_ones,
        day_of_month,
        month_name,
        year,
    )


def sync_NTP():
    if OFFLINE_MODE:
        # Generate random values for hours, minutes, and seconds
        hours = random.randint(0, 23)
        minutes = random.randint(0, 59)
        seconds = random.randint(0, 59)
        utils.log_message(
            f"Offline mode: setting a random time {hours:02d}:{minutes:02d}:{seconds:02d}"
        )

        # Set the RTC to the random time
        machine.RTC().datetime((2023, 1, 1, 0, hours, minutes, seconds, 0))
    elif not utils.is_wifi_connected():
        raise OSError("Wifi not connected")

    try:
        ntptime.settime()
        utils.log_message("RTC set from NTP", level="INFO")
    except Exception as e:
        utils.log_message(f"Failed to set RTC from NTP: {e}", level="ERROR")


async def check_DST():
    try:
        # Get the current time from utime
        current_timestamp = utime.time()
        # Get the current time from the RTC
        rtc_timestamp = machine.RTC().datetime()

        # Rearrange the rtc_timestamp to match the format expected by utime.mktime()
        rtc_timestamp_rearranged = (
            rtc_timestamp[0],
            rtc_timestamp[1],
            rtc_timestamp[2],
            rtc_timestamp[4],
            rtc_timestamp[5],
            rtc_timestamp[6],
            rtc_timestamp[3],
            0,
        )

        # Convert the RTC timestamp to seconds since the Epoch
        rtc_timestamp_seconds = utime.mktime(rtc_timestamp_rearranged)

        # Check if DST is in effect
        is_DST_flag = is_DST(current_timestamp)

        # If DST is in effect, add an hour to the current timestamp
        if is_DST_flag:
            current_timestamp += 3600

        # If the current timestamp and the RTC timestamp differ by more than a minute,
        # update the RTC
        if abs(current_timestamp - rtc_timestamp_seconds) > 60:
            # rtc.datetime() param is a different format of tuple to utime.localtime() so below converts it
            machine.RTC().datetime(
                (
                    utime.localtime(current_timestamp)[0],
                    utime.localtime(current_timestamp)[1],
                    utime.localtime(current_timestamp)[2],
                    utime.localtime(current_timestamp)[6],
                    utime.localtime(current_timestamp)[3],
                    utime.localtime(current_timestamp)[4],
                    utime.localtime(current_timestamp)[5],
                    0,
                )
            )
            utils.log_message(
                f"RTC time updated for DST: {is_DST_flag}",
                level="INFO",
            )
        else:
            utils.log_message(
                f"RTC time not updated for DST, no change from: {is_DST_flag}",
                level="DEBUG",
            )
    except Exception as e:
        utils.log_message(
            f"Failed to set RTC {'from NTP' if sync_with_ntp else 'locally'}: {e}"
        )
