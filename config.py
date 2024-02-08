"""
Author: Adam Knowles
Version: 0.1
Name: config.py
Description: Config variables for main program.

GitHub Repository: https://github.com/Pharkie/picow-railway-departure
License: GNU General Public License (GPL)
"""

# Using const() to save memory wherever values will not change during
# execution (not needed for strings).
import re
import asyncio
from micropython import const
from machine import Pin


def parse_url(url):
    """
    Parses a URL into its components.

    This function uses a regular expression to parse the URL into its components: protocol,
    host, URI, and query string. If the URL does not match the regular expression, a ValueError
    is raised.

    Parameters:
    url (str): The URL to parse.

    Returns:
    tuple: A tuple containing the protocol, host, URI, and query string of the URL.

    Raises:
    ValueError: If the URL does not match the regular expression.
    """
    pattern = "^(https?):\\/\\/([^\\/]+)\\/([^\\?]*)(\\?(.*))?"
    match = re.match(pattern, url)

    if match is None:
        raise ValueError(f"Invalid URL: {url}")

    protocol = match.group(1)
    host = match.group(2)
    uri = match.group(3)
    query_string = match.group(5) or ""

    return protocol, host, uri, query_string


# OFFLINE_MODE = True  # Set to True to use sample_data.json instead of the live API.
OFFLINE_MODE = False  # Comment out one or the other

LOG_LEVEL = "DEBUG"  # Options: "INFO", "DEBUG", "ERROR".

# Set to 'RailDataOrg' or 'AWS'. First uses LDWS API, second uses AWS API Gateway below.
# API_SOURCE = 'RailDataOrg' # Comment out one or the other
API_SOURCE = "AWS"  # Comment out one or the other

STATION_CRS = "PMW"  # Station's CRS code

# Number of services to request (0-10) from Rail Data API
# The risk is that services for the requested platform(s) may not appear in the first X results.
# The AWS intermediary API solves this.
RAILDATAORG_NUMBER_OF_SERVICES = const(6)

OFFLINE_JSON_FILE = "sample_data.json"  # File to use for offline mode

FONTDRAWER_FONT_NAME = "dejav_m10"  # Font for text

# Set to None to disable
# CUSTOM_TRAVEL_ALERT = (
#     "This is a 100 character long test travel alert for testing purposes. "
#     "Please ignore. 12345"
# )

# I2C pins for OLED screens
OLED1_SCL_PIN = Pin(17)  # Blue
OLED1_SDA_PIN = Pin(16)  # Green
OLED2_SCL_PIN = Pin(19)  # Blue
OLED2_SDA_PIN = Pin(18)  # Green

RAILDATAORG_API_URL = (  # National Rail API URL. On two lines for readability.
    "https://api1.raildata.org.uk"
    "/1010-live-departure-board-dep/LDBWS/api/20220120/GetDepBoardWithDetails"
)

# No idea if this works for Platform A etc (e.g. at PAD).
OLED1_PLATFORM_NUMBER = (
    "1"  # Platform number to show departures for. Note: string not an integer.
)
OLED2_PLATFORM_NUMBER = (
    "2"  # Platform number to show departures for. Note: string not an integer.
)

AWS_PLATFORMS_TO_GET = ",".join([OLED1_PLATFORM_NUMBER, OLED2_PLATFORM_NUMBER])

# Specify the full API URL and the code will parse it into components.
AWS_API_URL = (
    f"https://kmm1ogta93.execute-api.eu-west-2.amazonaws.com/prod/{STATION_CRS}"
    + f"?platforms={AWS_PLATFORMS_TO_GET}"
)

# Parse the URL into components
AWS_API_PROTOCOL, AWS_API_HOST, AWS_API_URI, AWS_API_QUERYSTRING = parse_url(
    AWS_API_URL
)

# These four are calculated, no need to set.
host_parts = AWS_API_HOST.split(".")
AWS_API_ID = host_parts[0]
AWS_API_SERVICE = host_parts[1]
AWS_API_REGION = host_parts[2]

BASE_API_UPDATE_INTERVAL = const(
    60
)  # Default update interval for rail data in seconds.
DATA_OUTDATED_SECS = const(
    80
)  # Rail data considered unusuable after this many seconds.

# OLED screen params (SSD1306)
LINEONE_Y = const(0)
THIN_LINETWO_Y = const(11)
THIN_LINETHREE_Y = const(22)

THICK_LINETWO_Y = const(12)
THICK_LINETHREE_Y = const(24)

DISPLAY_WIDTH = const(128)
DISPLAY_HEIGHT = const(32)

THIN_LINE_HEIGHT = const(10)
THICK_LINE_HEIGHT = const(12)

THIN_CHAR_WIDTH = const(6)  # Width of a thin character
THICK_CHAR_WIDTH = const(8)  # Width of a thick character

WIFI_TIMEOUT = const(20)  # Seconds
