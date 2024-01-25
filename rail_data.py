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
import display_utils


class RailData:
    def __init__(self):
        self.nrcc_message = ""
        self.oled1_departures = []
        self.oled2_departures = []
        self.get_rail_data_count = 0
        self.api_fails = 0
        self.api_retry_secs = config.BASE_API_UPDATE_INTERVAL

    async def fetch_data_from_api(self):
        assert utils.is_wifi_connected(), "Wifi not connected"
        rail_data_headers = {"x-apikey": credentials.RAILDATAORG_API_KEY}

        response = None
        # Exceptions are caught by the caller
        try:
            gc.collect()

            log_message("Calling API", level="DEBUG")

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
                raise ConnectionError("No response from API")

            if response.status_code < 200 or response.status_code >= 300:
                log_message(
                    f"HTTP request failed, status code {response.status_code}",
                    level="ERROR",
                )
                raise ConnectionError(
                    f"HTTP request failed, status code {response.status_code}"
                )

            # Log the size of the response data in KB, rounded to 2 decimal places
            log_message(f"API response: {round(len(response.content) / 1024, 2)} KB")

            json_data = ujson.loads(response.text)

            gc.collect()
            return json_data
        finally:
            if response:
                response.close()

    def get_departure_summary(self, departures):
        get_departure = lambda d: f"{d['destination']} ({d['time_scheduled']})"
        return (
            "No departures"
            if not departures
            else " and ".join(get_departure(d) for d in departures[:2])
        )

    def get_offline_rail_data(self):
        """
        Get data from a file.
        """
        self.get_rail_data_count += 1
        log_message(
            f"get_offline_rail_data call {self.get_rail_data_count}. Free memory: {gc.mem_free()}",  # pylint: disable=no-member
            level="DEBUG",
        )

        try:
            with open(config.OFFLINE_JSON_FILE, "r") as offline_data_file:
                response_JSON = ujson.load(offline_data_file)
        except OSError as e:
            log_message(f"Error opening or reading file: {e}", level="ERROR")
            raise
        except ValueError as e:
            log_message(f"Error loading file JSON: {e}", level="ERROR")
            raise

        self.parse_rail_data(response_JSON)
        gc.collect()

        oled1_summary = self.get_departure_summary(self.oled1_departures)
        oled2_summary = self.get_departure_summary(self.oled2_departures)

        log_message(
            f"[OFFLINE] get_offline_rail_data() got oled1_departures (Platform {config.OLED1_PLATFORM_NUMBER}): "
            + f"{oled1_summary} and oled2_departures (Platform {config.OLED2_PLATFORM_NUMBER}): {oled2_summary}",
            level="INFO",
        )

    async def get_online_rail_data(self, oled1, oled2):
        self.get_rail_data_count += 1
        log_message(
            f"get_online_rail_data call {self.get_rail_data_count}. Free memory: {gc.mem_free()}",  # pylint: disable=no-member
            level="DEBUG",
        )

        # Save the current screen contents
        oled1_before = oled1.save_buffer()
        oled2_before = oled2.save_buffer()

        display_utils.both_screen_text(oled1, oled2, "Updating trains", 12)

        response_JSON = await self.fetch_data_from_api()

        self.parse_rail_data(response_JSON)
        gc.collect()

        # Restore the displays
        oled1.restore_buffer(oled1_before)
        oled2.restore_buffer(oled2_before)
        oled1.show()
        oled2.show()

        oled1_summary = self.get_departure_summary(self.oled1_departures)
        oled2_summary = self.get_departure_summary(self.oled2_departures)

        log_message(
            f"[ONLINE] get_online_rail_data() got oled1_departures (Platform {config.OLED1_PLATFORM_NUMBER}): "
            + f"{oled1_summary} and oled2_departures (Platform {config.OLED2_PLATFORM_NUMBER}): {oled2_summary}",
            level="DEBUG",
        )

    async def cycle_get_online_rail_data(self, oled1, oled2):
        """
        Updates rail data from the API every BASE_API_UPDATE_INTERVAL seconds.
        Next call backs off on API failure. Delays between API calls (in seconds):
        Retry wait in seconds: 5, 10, 20, 40, 80, 160, 180 (3 mins) capped.
        """
        self.api_retry_secs = config.BASE_API_UPDATE_INTERVAL

        while True:
            await asyncio.sleep(self.api_retry_secs)

            try:
                await self.get_online_rail_data(oled1, oled2)

                # If we get here, the API call succeeded
                self.api_fails = 0  # Reset the failure counter
                self.api_retry_secs = (
                    config.BASE_API_UPDATE_INTERVAL
                )  # Reset the retry delay

                log_message(
                    f"API request success. Next retry in {self.api_retry_secs} seconds.",
                    level="INFO",
                )
            except (ConnectionError, ValueError, TypeError, MemoryError) as e:
                self.api_fails += 1
                self.api_retry_secs = min(5 * 2 ** (self.api_fails - 1), 180)
                log_message(
                    f"API request fail #{self.api_fails}: {e}. Next retry in {self.api_retry_secs} seconds.",
                    level="ERROR",
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
                custom_travel_alert = getattr(config, "CUSTOM_TRAVEL_ALERT", None)
                if custom_travel_alert is not None:
                    self.nrcc_message = custom_travel_alert
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

    log_message("\n\n[Program started]\n")
    log_message(f"Using API: {config.API_SOURCE}")

    # Initiliase to None since not used?
    oled1, oled2 = None, None

    if utils.is_wifi_connected():
        ntptime.settime()
        rail_data_instance = RailData()

        loop_counter = 0

        await rail_data_instance.get_online_rail_data(oled1, oled2)
        asyncio.create_task(rail_data_instance.cycle_get_online_rail_data(oled1, oled2))

        while True:
            loop_counter += 1
            log_message(
                f"Loop {loop_counter}. Free memory: {gc.mem_free()}",  # pylint: disable=no-member
                level="DEBUG",
            )

            if loop_counter % 5 == 0:
                gc.collect()  # Fixes a memory leak someplace

            await asyncio.sleep(10)  # Pick a number
    else:
        log_message("No wifi connection. Exiting.", level="ERROR")


if __name__ == "__main__":
    asyncio.run(main())
