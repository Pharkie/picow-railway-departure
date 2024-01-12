STATION_CRS = "PMW"  # Station's CRS code

OLED1_PLATFORM_NUMBER = "1"  # Platform number to show departures for. Note: string not an integer.
OLED2_PLATFORM_NUMBER = "2"  # Platform number to show departures for. Note: string not an integer.

LDBWS_API_URL = ( # National Rail API URL. On two lines for readability.
    "https://api1.raildata.org.uk"
    "/1010-live-departure-board-dep/LDBWS/api/20220120/GetDepBoardWithDetails"
)

offline_mode = False  # Set to True to use sample_data.json instead of the live API. Not a constant since could be changed at runtime.

# OLED screen params (SSD1306)
LINEONE_Y = 0
THIN_LINETWO_Y = 11
THIN_LINETHREE_Y = 22

THICK_LINETWO_Y = 12
THICK_LINETHREE_Y = 24

DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 32

THIN_LINE_HEIGHT = 10
THICK_LINE_HEIGHT = 12

THIN_CHAR_WIDTH = 6  # Width of a thin character
THICK_CHAR_WIDTH = 8  # Width of a thick character

WIFI_TIMEOUT = 20  # Seconds