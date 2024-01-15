import re
import uaiohttpclient
import uasyncio as asyncio
import ujson
import utime
import micropython
import gc
import utils
import config
import credentials

class RailData:
    def __init__(self):
        # self.nrcc_message = "Some long sample text would go here if there was a possibility that there were problems on the rail network somewhere I think?"
        self.nrcc_message = ""
        self.oled1_departures = []
        self.oled2_departures = []
  
    async def fetch_data_from_api(self, max_retries=3, retry_seconds=3):
        assert utils.is_wifi_connected(), "Wifi not connected"
        api_url = f"{config.LDBWS_API_URL}/{config.STATION_CRS}"
        request_headers = {"x-apikey": credentials.LDBWS_API_KEY}

        response = None
        for i in range(max_retries):
            try:
                print(f"Fetching api data. System uptime: {utime.ticks_ms() // 3600000:02}:{(utime.ticks_ms() // 60000) % 60:02}:{(utime.ticks_ms() // 1000) % 60:02}") # Debug print
                print("Loading API data. GC BEFORE attempt:")
                gc.collect() # Seems to help make space for the response in memory
                micropython.mem_info()

                response = await uaiohttpclient.request("GET", api_url)
                
                json_data = await response.json()

                # Parse the JSON data
                if json_data:
                    train_services = json_data.get("trainServices")
                    if train_services:
                        self.oled1_departures = self.parse_departures(train_services, config.OLED1_PLATFORM_NUMBER)
                        self.oled2_departures = self.parse_departures(train_services, config.OLED2_PLATFORM_NUMBER)

                    if getattr(config, 'CUSTOM_TRAVEL_ALERT', None) is not None: # Check if CUSTOM_TRAVEL_ALERT is defined in config.py
                        self.nrcc_message = config.CUSTOM_TRAVEL_ALERT

                    # Break out of the For loop and finish
                    return
            except OSError as e:
                if e.args[0] == 110:  # ETIMEDOUT
                    print(f"Rail data API request timed out. Attempt {i+1} of {max_retries}. Retry in {retry_seconds} seconds.")
                    await asyncio.sleep(retry_seconds)
                else:
                    print("Error sending request")
            except ValueError:
                print("Error parsing JSON response")
            finally:
                if response:
                    response.close()
                print("Loading API data. GC AFTER attempt:")
                gc.collect()
                micropython.mem_info()

    def fetch_data_from_file(self):
        try:
            gc.collect()  # Run the garbage collector
            print("Loading file data. Memory check:")
            micropython.mem_info()
            with open(config.OFFLINE_JSON_FILE, 'r') as offline_data_file:
                return ujson.load(offline_data_file)
        except OSError as e:
            print(f"Error opening or reading file: {e}")
            return None
        except ValueError as e:
            print(f"Error parsing JSON data: {e}")
            return None

    async def get_rail_data(self):
        """
        Get data from the National Rail API.
        """
        response_JSON = None

        try:
            if not config.offline_mode:
                await self.fetch_data_from_api()
            else:
                response_JSON = self.fetch_data_from_file()
                self.parse_rail_data(response_JSON)
        except Exception as e:
            print(f"Error fetching rail data: {e}. Switching to offline mode and cancelling updates.")
            response_JSON = self.fetch_data_from_file()
            self.parse_rail_data(response_JSON)
            config.offline_mode = True

        offline_status = 'OFFLINE' if config.offline_mode else 'ONLINE'
        get_departure = lambda d: f"{d['destination']} ({d.get('time_scheduled', 'N/A')})"
        oled1_summary = 'No departures' if not self.oled1_departures else ' and '.join(get_departure(d) for d in self.oled1_departures[:2])
        oled2_summary = 'No departures' if not self.oled2_departures else ' and '.join(get_departure(d) for d in self.oled2_departures[:2])

        # print(
        #     f"[{offline_status}] get_rail_data() got oled1_departures (Platform {config.OLED1_PLATFORM_NUMBER}): " +
        #     f"{oled1_summary} and oled2_departures (Platform {config.OLED2_PLATFORM_NUMBER}): {oled2_summary}"
        # )

        print(
            f"[{offline_status}] get_rail_data() got oled1_departures: {self.oled1_departures}" +
            f"{oled1_summary} and oled2_departures: {self.oled2_departures}"
        )

    def parse_service(self, service):
        return {
            "destination": service.get("destination", [{}])[0].get("locationName"),
            "time_scheduled": service.get("std"),
            "time_estimated": service.get("etd"),
            "operator": service.get("operator"),
            # "subsequentCallingPoints": [
            #     (
            #         calling_point.get("locationName"),
            #         calling_point.get("et") if calling_point.get("et") != "On time" else calling_point.get("st"),
            #     ) for calling_point in service.get("subsequentCallingPoints", [{}])[0].get("callingPoint", [])
            # ]
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
                    self.oled1_departures = self.parse_departures(train_services, config.OLED1_PLATFORM_NUMBER)
                    self.oled2_departures = self.parse_departures(train_services, config.OLED2_PLATFORM_NUMBER)
                    # For testing purposes
                    # self.oled1_departures[1] = self.oled1_departures[0] # Hack to make the second departure the same as the first
                    # self.oled1_departures[0]['subsequentCallingPoints'] = [{'locationName': "testy test", 'time_due': "21:30"}]
                    # self.oled1_departures[1]['subsequentCallingPoints'] = [{'locationName': "testy test", 'time_due': "21:30"}]
                    # print(f"OLED1 departures: {self.oled1_departures}")  # Debug print
                    # print(f"OLED2 departures: {self.oled2_departures}")  # Debug print

                if getattr(config, 'CUSTOM_TRAVEL_ALERT', None) is not None: # Check if CUSTOM_TRAVEL_ALERT is defined in config.py
                    self.nrcc_message = config.CUSTOM_TRAVEL_ALERT
                else:
                    self.nrcc_message = self.parse_nrcc_message(data_JSON.get("nrccMessages"))
        except Exception as e:
            print(f"An error occurred while parsing rail data: {e}")
    
if __name__ == "__main__":
    # utils.connect_wifi()
    rail_data_instance = RailData()  # Replace RailData with the actual class name
    print(rail_data_instance.get_rail_data())