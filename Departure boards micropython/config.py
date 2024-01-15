# Using const() to save memory wherever values will not change during execution
from micropython import const
from machine import Pin
STATION_CRS = "PMW"  # Station's CRS code

offline_mode = True  # Set to True to use sample_data.json instead of the live API. Not a constant since could be changed at runtime.

OLED1_PLATFORM_NUMBER = "1"  # Platform number to show departures for. Note: string not an integer.
OLED2_PLATFORM_NUMBER = "2"  # Platform number to show departures for. Note: string not an integer.

CUSTOM_TRAVEL_ALERT = "This is a 100 character long test travel alert for testing purposes. Please ignore. 12345"  # Set to None to disable

# I2C pins for OLED screens
OLED1_SCL_PIN = Pin(17)
OLED1_SDA_PIN = Pin(16)
OLED2_SCL_PIN = Pin(19)
OLED2_SDA_PIN = Pin(18)

LDBWS_API_URL = ( # National Rail API URL. On two lines for readability.
    "https://api1.raildata.org.uk"
    "/1010-live-departure-board-dep/LDBWS/api/20220120/GetDepBoardWithDetails"
)

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
