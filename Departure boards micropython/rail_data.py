import re
import urequests
import uasyncio as asyncio
import utils
import json
from credentials import LDBWS_API_KEY
from config import STATION_CRS, LDBWS_API_URL, OLED1_PLATFORM_NUMBER, OLED2_PLATFORM_NUMBER, offline_mode

class RailData:
    def __init__(self):
        # self.nrcc_message = "Some long sample text would go here if there was a possibility that there were problems on the rail network somewhere I think?"
        self.nrcc_message = ""
        self.oled1_departures = []

    async def get_rail_data(self):
        """
        Get data from the National Rail API.
        """
        global offline_mode
        response_JSON = None

        # Get data
        if not offline_mode:
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
            except Exception as e:
                print(f"Error fetching rail data: {e}. Switching to offline mode.")
                offline_mode = True
        elif offline_mode:
            try:
                with open("sample_data.json", "r") as sample_data_file:
                    response_JSON = json.load(sample_data_file)
            except FileNotFoundError:
                print("Error: could not find file 'sample_data.json'.")
            except IOError as e:
                print(f"Error: problem reading 'sample_data.json': {e}")

        # Parse data and load into class variables
        self.parse_rail_data(response_JSON)

        # print(f"get_rail_data() got departures_list: {self.departures_list}")
        print(f"get_rail_data() got {len(self.oled1_departures)} services for oled1_departures and {len(self.oled2_departures)} services for oled2_departures")

    def parse_service(self, service):
        return {
            "destination": service.get("destination", [{}])[0].get("locationName"),
            "time_scheduled": service.get("std"),
            "time_estimated": service.get("etd"),
            "operator": service.get("operator"),
            "subsequentCallingPoints": [
                {
                    "locationName": calling_point.get("locationName"),
                    "time_due": calling_point.get("et") if calling_point.get("et") != "On time" else calling_point.get("st"),
                } for calling_point in service.get("subsequentCallingPoints", [{}])[0].get("callingPoint", [])
            ]
        }

    def parse_departures(self, train_services, platform_number):
        return [
            self.parse_service(service) for service in train_services if service.get("platform") == platform_number
        ][:2]

    def parse_nrcc_message(self, nrcc_messages):
        if nrcc_messages:
            nrcc_message = nrcc_messages[0].get("Value", "")
            return re.sub('<.*?>', '', nrcc_message)
        return ""

    def parse_rail_data(self, data_JSON):
        """
        Parse the rail data to get the first two departures for the station and platform specified in config.py
        Within the next 120 minutes (default/max)
        Plus any NRCC Travel Alert message.
        """
        try:
            if data_JSON:
                train_services = data_JSON.get("trainServices")
                if train_services:
                    # print(f"All services: {train_services}")  # Debug print
                    self.oled1_departures = self.parse_departures(train_services, OLED1_PLATFORM_NUMBER)
                    self.oled2_departures = self.parse_departures(train_services, OLED2_PLATFORM_NUMBER)
                    # print(f"OLED1 departures: {self.oled1_departures}")  # Debug print
                    # print(f"OLED2 departures: {self.oled2_departures}")  # Debug print

                self.nrcc_message = self.parse_nrcc_message(data_JSON.get("nrccMessages"))
        except Exception as e:
            print(f"An error occurred while parsing rail data: {e}")
    
if __name__ == "__main__":
    # utils.connect_wifi()
    rail_data_instance = RailData()  # Replace RailData with the actual class name
    print(rail_data_instance.get_rail_data())