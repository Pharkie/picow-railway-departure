import re
import requests
import asyncio
import ujson
import gc
import utils
import config
import credentials
from utils import log_message
import aws_api


class RailData:
    def __init__(self):
        self.nrcc_message = ""
        self.oled1_departures = []
        self.oled2_departures = []
        self.get_rail_data_count = 0

    async def fetch_data_from_api(self, max_retries=3):
        assert utils.is_wifi_connected(), "Wifi not connected"
        rail_data_headers = {"x-apikey": credentials.RAILDATAORG_API_KEY}

        for i in range(max_retries):
            response = None
            try:
                gc.collect()
                if config.API_SOURCE == "RailDataOrg":
                    rail_data_url = (
                        f"{config.RAILDATAORG_API_URL}/{config.STATION_CRS}"
                        + f"?numRows={config.RAILDATAORG_NUMBER_OF_SERVICES}"
                    )
                    response = requests.get(
                        url=rail_data_url, headers=rail_data_headers, timeout=10
                    )
                elif config.API_SOURCE == "AWS":
                    rail_data_headers = aws_api.create_signed_headers(
                        api_host=config.AWS_API_HOST,
                        api_uri=config.AWS_API_URI,
                        region=config.AWS_API_REGION,
                        service=config.AWS_API_SERVICE,
                        access_key=credentials.AWS_ACCESS_KEY,
                        secret_key=credentials.AWS_SECRET_ACCESS_KEY,
                        query_string=config.AWS_API_QUERYSTRING,
                        additional_headers=rail_data_headers,
                    )

                    response = requests.get(
                        url=config.AWS_API_URL, headers=rail_data_headers, timeout=10
                    )

                if not response:
                    log_message("No response from API", level="ERROR")
                    raise OSError("No response from API")

                if response.status_code < 200 or response.status_code >= 300:
                    log_message(
                        f"HTTP request failed, status code {response.status_code}",
                        level="ERROR",
                    )
                    raise OSError(
                        "HTTP request failed, status code {response.status_code}"
                    )

                # Log the size of the response data in KB, rounded to 2 decimal places
                log_message(
                    f"API response: {round(len(response.content) / 1024, 2)} KB"
                )

                json_data = ujson.loads(response.text)

                gc.collect()
                return json_data
            except (OSError, ValueError, TypeError, MemoryError) as e:
                log_message(
                    f"Error with request to API on attempt {i+1}: {e}", level="ERROR"
                )
                if i < max_retries - 1:  # No delay after the last attempt
                    await asyncio.sleep(2**i)  # Exponential backoff
                raise e  # Re-raise the exception to stop the program.

            finally:
                if response:
                    response.close()

    def fetch_data_from_file(self):
        try:
            with open(config.OFFLINE_JSON_FILE, "r") as offline_data_file:
                return ujson.load(offline_data_file)
        except OSError as e:
            log_message(f"Error opening or reading file: {e}", level="ERROR")
            return None
        except ValueError as e:
            log_message(f"Error loading file JSON: {e}", level="ERROR")
            return None

    async def get_rail_data(self):
        """
        Get data from the National Rail API.
        """
        self.get_rail_data_count += 1
        log_message(
            f"get_rail_data call {self.get_rail_data_count}. Free memory: {gc.mem_free()}",
            level="DEBUG",
        )

        response_JSON = None

        if config.OFFLINE_MODE:
            response_JSON = self.fetch_data_from_file()
        else:
            response_JSON = await self.fetch_data_from_api()

        # log(f"\nresponse_JSON: {response_JSON}\n")  # Debug print

        self.parse_rail_data(response_JSON)
        gc.collect()

        offline_status = "OFFLINE" if config.OFFLINE_MODE else "ONLINE"
        get_departure = lambda d: f"{d['destination']} ({d['time_scheduled']})"
        oled1_summary = (
            "No departures"
            if not self.oled1_departures
            else " and ".join(get_departure(d) for d in self.oled1_departures[:2])
        )
        oled2_summary = (
            "No departures"
            if not self.oled2_departures
            else " and ".join(get_departure(d) for d in self.oled2_departures[:2])
        )

        log_message(
            f"[{offline_status}] get_rail_data() got oled1_departures (Platform {config.OLED1_PLATFORM_NUMBER}): "
            + f"{oled1_summary} and oled2_departures (Platform {config.OLED2_PLATFORM_NUMBER}): {oled2_summary}",
            level="DEBUG",
        )

    def parse_service(self, service):
        if not service:
            raise ValueError("service is required")

        subsequentCallingPoints = [
            (
                calling_point.get("locationName"),
                calling_point.get("et")
                if calling_point.get("et") != "On time"
                else calling_point.get("st"),
            )
            for subsequent_calling_point in service.get("subsequentCallingPoints", [])
            for calling_point in subsequent_calling_point.get("callingPoint", [])
        ]

        return {
            "destination": service.get("destination", [{}])[0].get("locationName"),
            "time_scheduled": service.get("std"),
            "time_estimated": service.get("etd"),
            "operator": service.get("operator"),
            "subsequentCallingPoints": subsequentCallingPoints,
        }

    def parse_departures(self, train_services, platform_number):
        """
        Parses the departures from the provided train services data for a specific platform.

        Iterates over the train services data and extracts relevant
        information about the departures that are departing from the platform specified by
        the platform_number.

        Args:
            train_services (list): A list of dictionaries, each representing a train service.
            platform_number (str): The platform number to filter the departures by.

        Returns:
            list: A list of dictionaries, each representing a parsed train service departing from the specified platform.
        """
        if not train_services:
            raise ValueError("train_services is required")

        if not platform_number:
            raise ValueError("platform_number is required")

        # Parse each service in the train services list
        return [
            self.parse_service(service)
            for service in train_services
            if service.get("platform") == platform_number
        ][:2]

    def parse_nrcc_message(self, nrcc_messages=None):
        """
        Parses the NRCC messages from the provided data.

        Args:
            nrcc_messages (list): A list of dictionaries, each representing an NRCC message.

        Returns:
            str: A string representing the parsed NRCC message.
        """
        if nrcc_messages:
            nrcc_message = nrcc_messages[0].get("Value", "")
            return re.sub("<.*?>", "", nrcc_message)
        return ""

    def parse_rail_data(self, data_JSON):
        """
        Parse the rail data to get the first two departures for the station and platform specified in config.py
        Within the next 120 minutes (default/max)
        Plus any NRCC Travel Alert message.
        """
        try:
            if data_JSON:
                train_services = data_JSON.get("trainServices", [])

                # log(f"Train services: {json.dumps(train_services)}")  # Debug print
                self.oled1_departures = (
                    self.parse_departures(train_services, config.OLED1_PLATFORM_NUMBER)
                    if train_services
                    else []
                )

                self.oled2_departures = (
                    self.parse_departures(train_services, config.OLED2_PLATFORM_NUMBER)
                    if train_services
                    else []
                )

                # Check if CUSTOM_TRAVEL_ALERT is defined in config.py
                if getattr(config, "CUSTOM_TRAVEL_ALERT", None):
                    self.nrcc_message = config.CUSTOM_TRAVEL_ALERT
                else:
                    if data_JSON.get("nrccMessages"):
                        self.nrcc_message = self.parse_nrcc_message(
                            data_JSON.get("nrccMessages")
                        )
        except Exception as e:
            log_message(f"Error parsing rail data JSON: {e}", level="ERROR")


async def main():
    import ntptime

    utils.connect_wifi()

    log_message("\n\n[Program started]\n", level="INFO")
    log_message(f"Using API: {config.API_SOURCE}", level="INFO")

    if utils.is_wifi_connected():
        ntptime.settime()
        rail_data_instance = RailData()

        loop_counter = 0

        while True:
            loop_counter += 1
            log_message(
                f"Loop {loop_counter}. Free memory: {gc.mem_free()}", level="DEBUG"
            )

            if loop_counter % 5 == 0:
                gc.collect()  # Fixes a memory leak someplace

            await rail_data_instance.get_rail_data()

            await asyncio.sleep(0.5)
    else:
        log_message("No wifi connection. Exiting.", level="ERROR")


if __name__ == "__main__":
    asyncio.run(main())
