import re
import urequests
import uasyncio as asyncio
import utils
from credentials import LDBWS_API_KEY
from config import STATION_CRS, LDBWS_API_URL, PLATFORM_NUMBER

class RailData:
    def __init__(self):
        self.nrcc_message = ""
        self.departures_list = []

    async def get_rail_data(self):
        """
        Get data from the National Rail API.
        """
        if not utils.is_wifi_connected():
            raise Exception("Wi-Fi is not connected")
        
        response_JSON = None
        
        try:
            api_url = f"{LDBWS_API_URL}/{STATION_CRS}"
            request_headers = {"x-apikey": LDBWS_API_KEY}
            response = urequests.get(url=api_url, headers=request_headers, timeout=10)
            response_JSON = response.json()

            # Essential or we get ENOMEM errors. Don't switch for one line responseJSON = urequests.get().json()
            response.close()

            self.nrcc_message = self.get_nrcc_msg(response_JSON) # TODO: Show this on the display
            self.departures_list = self.get_departures(response_JSON)

            print(f"get_ldbws_data() got departures_list: {self.departures_list}")
        except Exception as e:
            print(f"Error fetching LDBWS data: {e}")

    def get_departures(self, api_data):
        """
        Get the first two departures from the National Rail API for the station and platform specified.
        """
        if api_data and "trainServices" in api_data:
            num_departures = min(2, len(api_data["trainServices"]))
            departures = [{
                "destination": api_data["trainServices"][i]["destination"][0]["locationName"],
                "time_due": api_data["trainServices"][i]["std"],
                "subsequentCallingPoints": [
                    {
                        "locationName": calling_point["locationName"],
                        "time_due": calling_point["st"]
                    } for calling_point in api_data["trainServices"][i]["subsequentCallingPoints"][0]["callingPoint"]
                ]
            } for i in range(num_departures) if api_data["trainServices"][i]["platform"] == PLATFORM_NUMBER]
            return departures
        else:
            return []

    def get_nrcc_msg(self, api_data):
        """
        Get any NRCC message
        """
        if api_data and "nrccMessages" in api_data and api_data["nrccMessages"]:
            # Get the NRCC message
            nrcc_message = api_data["nrccMessages"][0]["Value"]
            # Remove HTML tags
            nrcc_message = re.sub('<.*?>', '', nrcc_message)
            return nrcc_message
        else:
            return ""
    
if __name__ == "__main__":
    utils.connect_wifi()
    print(get_ldbws_data())