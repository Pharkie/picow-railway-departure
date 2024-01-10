import urequests
import re
import utils
import uasyncio as asyncio
import urandom
from credentials import LDBWS_API_KEY
from config import STATION_CRS, LDBWS_API_URL

def get_ldbws_api_data():
    """
    Function to get data from the National Rail API.
    """
    if not utils.is_wifi_connected():
        raise Exception("Wi-Fi is not connected")
    
    response_JSON = None
    
    try:
        url = f"{LDBWS_API_URL}/{STATION_CRS}"
        headers = {"x-apikey": LDBWS_API_KEY}
        response = urequests.get(url, headers=headers, timeout=10)
        response_JSON = response.json()

        # Essential or we get ENOMEM errors. Don't switch for one line responseJSON = urequests.get().json()
        response.close()

        print("LDBWS data refreshed")
    except Exception as e:
        print(f"Error fetching data: {e}")

    return response_JSON

def get_departures(api_data):
    """
    Get the first two departures from the National Rail API for the station and platform specified.
    """
    if api_data and "trainServices" in api_data:
        # Get up to the first two departures
        num_departures = min(2, len(api_data["trainServices"]))
        departures = [{
            "destination": api_data["trainServices"][i]["destination"][0]["locationName"],
            "time_due": api_data["trainServices"][i]["std"],
            "platform": api_data["trainServices"][i]["platform"]
        } for i in range(num_departures) if api_data["trainServices"][i]["platform"] == config.PLATFORM_NUMBER]
        return departures
    else:
        return []

def get_nrcc_msg(api_data):
    """
    Function to get the NRCC message from the National Rail API.
    """
    if api_data and "nrccMessages" in api_data and api_data["nrccMessages"]:
        # Get the NRCC message
        nrcc_message = api_data["nrccMessages"][0]["Value"]
        # Remove HTML tags
        nrcc_message = re.sub('<.*?>', '', nrcc_message)
        return nrcc_message
    else:
        return ""
    
async def sync_ldbws_periodically():
    global ldbws_api_data

    while True:
        # print("sync_ldbws_periodically called")
        ldbws_api_data = get_ldbws_api_data()
         
        # Check again in 1-2 minutes
        next_sync_secs = urandom.randint(59, 119)
        
        print(f"sync_ldbws_periodically complete. Next sync in: {next_sync_secs} secs")
        await asyncio.sleep(next_sync_secs)  # Sleep for the calculated duration