STATION_CRS = "PMW"  # Station's CRS code

PLATFORM_NUMBER = "2"  # Platform number to show departures for. Note: string not an integer.

LDBWS_API_URL = ( # National Rail API URL. On two lines for readability.
    "https://api1.raildata.org.uk"
    "/1010-live-departure-board-dep/LDBWS/api/20220120/GetDepBoardWithDetails"
)

# OLED screen params (SSD1306)
LINEONE_Y = 0
LINETWO_Y = 12
LINETHREE_Y = 24

DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 32
LINE_HEIGHT = 12
CHAR_WIDTH = 8  # Width of a character in pixels

WIFI_TIMEOUT = 20  # Seconds

# INFO_STRINGS = [
#     "Be alert. See it. Say it. Sorted.",
#     "Mind the gap",
#     "Stand behind the yellow line",
#     "Please have your ticket ready",
# ]