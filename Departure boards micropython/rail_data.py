import re
import urequests
import uasyncio as asyncio
import utils
from credentials import LDBWS_API_KEY
from config import STATION_CRS, LDBWS_API_URL, PLATFORM_NUMBER, LINEONE_Y

class RailData:
    def __init__(self):
        # self.nrcc_message = "Some long sample text would go here if there was a possibility that there were problems on the rail network somewhere I think?"
        self.nrcc_message = ""
        self.departures_list = []

    async def get_rail_data(self):
        """
        Get data from the National Rail API.
        """
        response_JSON = None

        try:
            assert utils.is_wifi_connected(), "Wifi not connected"
               
            api_url = f"{LDBWS_API_URL}/{STATION_CRS}"
            request_headers = {"x-apikey": LDBWS_API_KEY}
            response = urequests.get(url=api_url, headers=request_headers, timeout=10)
            response_JSON = response.json()

            # Essential or we get ENOMEM errors. Don't switch for one line responseJSON = urequests.get().json()
            response.close()
            del response # Free up memory

            # print(f"get_rail_data() got response: {response_JSON}")

            parsed_data = self.parse_api_data(response_JSON)
            self.nrcc_message = parsed_data["nrcc_message"]
            self.departures_list = parsed_data["departures"]

            # print(f"get_rail_data() got departures_list: {self.departures_list}")
            print(f"get_rail_data() got info for {len(self.departures_list)} departures")
        except Exception as e:
            print(f"Error fetching LDBWS rail data: {e}")

    def parse_api_data(self, api_data):
        """
        Get the first two departures and any NRCC message from the National Rail API for the station and platform specified.
        """
        parsed_data = {"departures": [], "nrcc_message": ""}

        if api_data:
            train_services = api_data.get("trainServices")
            if train_services:
                num_departures = min(2, len(train_services))
                parsed_data["departures"] = [{
                    "destination": train_services[i].get("destination", [{}])[0].get("locationName"),
                    "time_due": train_services[i].get("std"),
                    "subsequentCallingPoints": [
                        {
                            "locationName": calling_point.get("locationName"),
                            "time_due": calling_point.get("st")
                        } for calling_point in train_services[i].get("subsequentCallingPoints", [{}])[0].get("callingPoint", [])
                    ]
                } for i in range(num_departures) if train_services[i].get("platform") == PLATFORM_NUMBER]

            nrcc_messages = api_data.get("nrccMessages")
            if nrcc_messages:
                # Get the NRCC message
                parsed_data["nrcc_message"] = nrcc_messages[0].get("Value", "")
                # Remove HTML tags
                parsed_data["nrcc_message"] = re.sub('<.*?>', '', parsed_data["nrcc_message"])

        return parsed_data
    
if __name__ == "__main__":
    # utils.connect_wifi()
    setup_display()
    rail_data_instance = RailData()  # Replace RailData with the actual class name
    print(rail_data_instance.get_rail_data())