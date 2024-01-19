# Using const() to save memory wherever values will not change during execution (not needed for strings).
from micropython import const
from machine import Pin
import re

def parse_url(url):
    pattern = '^(https?):\\/\\/([^\\/]+)\\/([^\\?]*)(\\?(.*))?'
    match = re.match(pattern, url)

    if match is None:
        raise ValueError(f"Invalid URL: {url}")

    protocol = match.group(1)
    host = match.group(2)
    uri = match.group(3)
    query_string = match.group(5) or ""

    return protocol, host, uri, query_string

# Set to 'RailDataOrg' or 'AWS'. First uses LDWS API, second uses AWS API Gateway below.
API_SOURCE = 'AWS'

STATION_CRS = "PMW"  # Station's CRS code

# Number of services to request (0-10). 
# The risk is that services for the requested platform(s) may not appear in the first X results.
# With this API (and others I looked at) there's ** no way to ask for services only from a given platform **.
# We want a small number (e.g. 4) for a large station (e.g. EUS), but could maybe afford a larger number for a small station.
# API responses over 50kb become likely to run out of memory and crash out.
# Finding a query that works for a given station may require adjustments to the query and parsing of the JSON to keep processing
# within Pico's limited memory e.g. adding a "To" filter to the query.
# The comprehensive alternative would be to create an Amazon Lambda function to query the API and
# return a filtered response via the Amazon API Gateway.
RAILDATAORG_NUMBER_OF_SERVICES = const(6)

# offline_mode = True  # Set to True to use sample_data.json instead of the live API.
offline_mode = False  # Comment out one or the other

OFFLINE_JSON_FILE = "sample_data_big.json"  # File to use for offline mode

# No idea if this works for Platform A etc (e.g. at PAD).
OLED1_PLATFORM_NUMBER = "1"  # Platform number to show departures for. Note: string not an integer.
OLED2_PLATFORM_NUMBER = "2"  # Platform number to show departures for. Note: string not an integer.

# CUSTOM_TRAVEL_ALERT = "This is a 100 character long test travel alert for testing purposes. Please ignore. 12345"  # Set to None to disable

# I2C pins for OLED screens
OLED1_SCL_PIN = Pin(17)
OLED1_SDA_PIN = Pin(16)
OLED2_SCL_PIN = Pin(19)
OLED2_SDA_PIN = Pin(18)

RAILDATAORG_API_URL = ( # National Rail API URL. On two lines for readability.
    "https://api1.raildata.org.uk"
    "/1010-live-departure-board-dep/LDBWS/api/20220120/GetDepBoardWithDetails"
)

# My idea here is you specify the full API URL you want to call and the code will parse it into its components.
AWS_PLATFORMS_TO_GET = "1,2"
AWS_API_URL = f"https://kmm1ogta93.execute-api.eu-west-2.amazonaws.com/prod/{STATION_CRS}?platforms={AWS_PLATFORMS_TO_GET}"

# Parse the URL into components
AWS_API_PROTOCOL, AWS_API_HOST, AWS_API_URI, AWS_API_QUERYSTRING = parse_url(AWS_API_URL)

host_parts = AWS_API_HOST.split('.')
AWS_API_ID = host_parts[0]
AWS_API_SERVICE = host_parts[1]
AWS_API_REGION = host_parts[2]

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
