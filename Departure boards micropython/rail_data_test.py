import re
import urequests
import asyncio
import ujson
import micropython
import gc
import utils
import config
import credentials
import utime
import ntptime

# Set global
# log_file = None

class OfflineModeException(Exception):
    def __init__(self, message="Application is in offline mode"):
        self.message = message
        super().__init__(self.message)

class RailData:
    def __init__(self):
        # self.nrcc_message = "Some long sample text would go here if there was a possibility that there were problems on the rail network somewhere I think?"
        self.nrcc_message = ""
        self.oled1_departures = []
        self.oled2_departures = []

    async def fetch_data_from_api(self, max_retries=3):
        assert utils.is_wifi_connected(), "Wifi not connected"
        api_url = f"{config.LDBWS_API_URL}/{config.STATION_CRS}"
        request_headers = {"x-apikey": credentials.LDBWS_API_KEY}

        for i in range(max_retries):
            response = None
            try:
                response = urequests.get(url=api_url, headers=request_headers, timeout=10)

                if response is None:
                    debug_message = "No response from API"
                    log(debug_message, level='ERROR')
                    raise OSError(debug_message)

                if response.status_code < 200 or response.status_code >= 300:
                    debug_message = f"HTTP request failed, status code {response.status_code}"
                    log(debug_message, level='ERROR')
                    raise OSError(debug_message)

                json_data = ujson.loads(response.text)

                gc.collect()
                return json_data
            except (OSError, ValueError, TypeError) as e:
                debug_message = f"Error with request to {api_url} on attempt {i+1}: {e}"
                log(debug_message, level='ERROR')
                if i < max_retries - 1:  # No delay after the last attempt
                    await asyncio.sleep(2 ** i)  # Exponential backoff
                raise e # Re-raise the exception to stop the program not recover, for debug.
                # else:
                #     raise
            finally:
                if response:
                    response.close()

    def fetch_data_from_file(self):
        try:
            # gc.collect()  # Run the garbage collector
            # print("Loading file data. Memory check:")
            # micropython.mem_info()
            with open(config.OFFLINE_JSON_FILE, 'r') as offline_data_file:
                return ujson.load(offline_data_file)
        except OSError as e:
            debug_message = f"Error opening or reading file: {e}"
            log(debug_message, level='ERROR')
            return None
        except ValueError as e:
            debug_message = f"Error parsing JSON data: {e}"
            log(debug_message, level='ERROR')
            return None

    async def get_rail_data(self):
        """
        Get data from the National Rail API.
        """
        response_JSON = None

        try:
            if not config.offline_mode:
                response_JSON = await self.fetch_data_from_api()
            else:
                raise OfflineModeException("Offline mode enabled")
        except (OSError, ValueError, MemoryError, OfflineModeException) as e:
            debug_message = f"Error fetching rail data: {e}. Free memory: {gc.mem_free()}. Switching to offline mode and cancelling updates."
            log(debug_message, level='ERROR')
            response_JSON = self.fetch_data_from_file()
            raise e  # Re-raise the exception to stop the program not recover, for debug.
            # config.offline_mode = True

        self.parse_rail_data(response_JSON)
        # del response_JSON
        gc.collect()
        # print("Loading data. GC AFTER attempt:")
        # gc.collect()
        # micropython.mem_info()

        offline_status = 'OFFLINE' if config.offline_mode else 'ONLINE'
        get_departure = lambda d: f"{d['destination']} ({d.get('time_scheduled', 'N/A')})"
        oled1_summary = 'No departures' if not self.oled1_departures else ' and '.join(get_departure(d) for d in self.oled1_departures[:2])
        oled2_summary = 'No departures' if not self.oled2_departures else ' and '.join(get_departure(d) for d in self.oled2_departures[:2])

        debug_message = (
            f"[{offline_status}] get_rail_data() got oled1_departures (Platform {config.OLED1_PLATFORM_NUMBER}): " +
            f"{oled1_summary} and oled2_departures (Platform {config.OLED2_PLATFORM_NUMBER}): {oled2_summary}"
        )
        log(debug_message, level='DEBUG')

        # print(
        #     f"[{offline_status}] get_rail_data() got oled1_departures: {self.oled1_departures} " +
        #     f"and oled2_departures: {self.oled2_departures}"
        # )

    def parse_service(self, service):
        if not service:
            return None  # or return a different default value

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
                oled1_platform_number = config.OLED1_PLATFORM_NUMBER
                oled2_platform_number = config.OLED2_PLATFORM_NUMBER
                if train_services:
                    # print(f"All services: {train_services}")  # Debug print
                    self.oled1_departures = self.parse_departures(train_services, oled1_platform_number)
                    self.oled2_departures = self.parse_departures(train_services, oled2_platform_number)
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
            debug_message = f"An error occurred while parsing rail data: {e}"
            log(debug_message, level='ERROR')

def log(message, level='INFO'):
    timestamp = utime.localtime(utime.time())
    formatted_timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*timestamp)
    log_message = f"{formatted_timestamp} [{level}]: {message}\n"

    print(log_message)
    log_file.write(log_message)

async def main():
    global log_file

    log_file = open('rail_data_log.txt', 'a')

    utils.connect_wifi()

    if utils.is_wifi_connected():
        ntptime.settime()
        rail_data_instance = RailData()

        loop_counter = 0

        try:
            while True:
                loop_counter += 1
                debug_message = f"Loop {loop_counter}. Free memory: {gc.mem_free()}"
                log(debug_message, level='DEBUG')

                await rail_data_instance.get_rail_data()

                await asyncio.sleep(0.5)
        finally:
            log_file.close()
    else:
        debug_message = "No wifi connection. Exiting."
        log(debug_message, level='ERROR')

if __name__ == "__main__":
    asyncio.run(main())
