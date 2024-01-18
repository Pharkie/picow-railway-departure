import re
import urequests
import asyncio
import ujson
import gc
import utils
import config
import credentials
from utils import log

class RailData:
    def __init__(self):
        self.nrcc_message = ""
        self.oled1_departures = []
        self.oled2_departures = []
        self.get_rail_data_count = 0

    async def fetch_data_from_api(self, max_retries=3):
        assert utils.is_wifi_connected(), "Wifi not connected"
        api_url = f"{config.LDBWS_API_URL}/{config.STATION_CRS}"
        request_headers = {"x-apikey": credentials.LDBWS_API_KEY}

        for i in range(max_retries):
            response = None
            try:
                gc.collect()
                response = urequests.get(url=api_url, headers=request_headers, timeout=10)

                if response is None:
                    log("No response from API", level='ERROR')
                    raise OSError(debug_message)

                if response.status_code < 200 or response.status_code >= 300:
                    log(f"HTTP request failed, status code {response.status_code}", level='ERROR')
                    raise OSError(debug_message)

                json_data = ujson.loads(response.text)

                gc.collect()
                return json_data
            except (OSError, ValueError, TypeError, MemoryError) as e:
                log(f"Error with request to {api_url} on attempt {i+1}: {e}", level='ERROR')
                if i < max_retries - 1:  # No delay after the last attempt
                    await asyncio.sleep(2 ** i)  # Exponential backoff
                raise e # Re-raise the exception to stop the program.

            finally:
                if response:
                    response.close()

    def fetch_data_from_file(self):
        try:
            with open(config.OFFLINE_JSON_FILE, 'r') as offline_data_file:
                return ujson.load(offline_data_file)
        except OSError as e:
            log(f"Error opening or reading file: {e}", level='ERROR')
            return None
        except ValueError as e:
            log(f"Error parsing JSON data: {e}", level='ERROR')
            return None

    async def get_rail_data(self):
        """
        Get data from the National Rail API.
        """
        self.get_rail_data_count += 1
        log(f"get_rail_data call {self.get_rail_data_count}. Free memory: {gc.mem_free()}", level='DEBUG')

        response_JSON = None

        if config.offline_mode:
            response_JSON = self.fetch_data_from_file()
        else:
            response_JSON = await self.fetch_data_from_api()

        self.parse_rail_data(response_JSON)
        gc.collect()

        offline_status = 'OFFLINE' if config.offline_mode else 'ONLINE'
        get_departure = lambda d: f"{d['destination']} ({d['time_scheduled']})"
        oled1_summary = 'No departures' if not self.oled1_departures else ' and '.join(get_departure(d) for d in self.oled1_departures[:2])
        oled2_summary = 'No departures' if not self.oled2_departures else ' and '.join(get_departure(d) for d in self.oled2_departures[:2])
        
        log(
            f"[{offline_status}] get_rail_data() got oled1_departures (Platform {config.OLED1_PLATFORM_NUMBER}): " +
            f"{oled1_summary} and oled2_departures (Platform {config.OLED2_PLATFORM_NUMBER}): {oled2_summary}", 
            level='DEBUG'
        )

    def parse_service(self, service):
        if not service:
            return None

        return {
            "destination": service.get("destination", [{}])[0].get("locationName"),
            "time_scheduled": service.get("std"),
            "time_estimated": service.get("etd"),
            "operator": service.get("operator"),
            "subsequentCallingPoints": [
                (
                    calling_point.get("locationName"),
                    calling_point.get("et") if calling_point.get("et") != "On time" else calling_point.get("st"),
                ) for calling_point in service.get("subsequentCallingPoints", [{}])[0].get("callingPoint", [])
            ]
        }

    def parse_departures(self, train_services, platform_number):
        if train_services is None:
            return []
        return [
            self.parse_service(service) for i, service in enumerate(train_services) if service.get("platform") == platform_number
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
                oled1_platform_number = config.OLED1_PLATFORM_NUMBER
                oled2_platform_number = config.OLED2_PLATFORM_NUMBER
                if train_services:
                    # print(f"All services: {train_services}")  # Debug print
                    self.oled1_departures = self.parse_departures(train_services, oled1_platform_number)
                    self.oled2_departures = self.parse_departures(train_services, oled2_platform_number)

                # Check if CUSTOM_TRAVEL_ALERT is defined in config.py
                if getattr(config, 'CUSTOM_TRAVEL_ALERT', None) is not None: 
                    self.nrcc_message = config.CUSTOM_TRAVEL_ALERT
                else:
                    self.nrcc_message = self.parse_nrcc_message(data_JSON.get("nrccMessages"))
        except Exception as e:
            log(f"Error occurred while parsing rail data: {e}", level='ERROR')

async def main():
    import ntptime
    utils.connect_wifi()

    if utils.is_wifi_connected():
        ntptime.settime()
        rail_data_instance = RailData()

        loop_counter = 0

        while True:
            loop_counter += 1
            log(f"Loop {loop_counter}. Free memory: {gc.mem_free()}", level='DEBUG')

            if loop_counter % 5 == 0:
                gc.collect()  # Fixes a memory leak someplace

            await rail_data_instance.get_rail_data()

            await asyncio.sleep(0.5)
    else:
        log("No wifi connection. Exiting.", level='ERROR')

if __name__ == "__main__":
    asyncio.run(main())
