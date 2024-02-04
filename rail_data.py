"""
Author: Adam Knowles
Version: 0.1
Name: rail_data.py
Description: Class for managing rail data. Fetches data from an API, handles offline data,
and updates the data periodically.

GitHub Repository: https://github.com/Pharkie/picow-railway-departure
License: GNU General Public License (GPL)
"""
import re
import asyncio
import gc
import requests
import ujson
import ntptime
import utils
import config
import credentials
from utils import log_message
import aws_api
import display_utils


class RailData:
    """
    This class is responsible for managing rail data. It fetches data from an API,
    handles offline data, and updates the data periodically.

    Attributes:
    nrcc_message: A string representing the NRCC message.
    oled1_departures: A list holding the departures for the first OLED display.
    oled2_departures: A list holding the departures for the second OLED display.
    get_rail_data_count: An integer representing the number of times rail data has been fetched.
    api_fails: An integer representing the number of times the API call has failed.
    api_retry_secs: An integer representing the number of seconds to wait before retrying
    the API call after a failure.

    Methods:
    fetch_data_from_api: Asynchronously fetches data from the API.
    get_departure_summary: Returns a summary of the departures.
    get_offline_rail_data: Fetches rail data from a file.
    get_online_rail_data: Asynchronously fetches rail data from the API and updates
    the OLED displays.
    cycle_get_online_rail_data: Continuously updates rail data from the API at a
    specified interval.
    parse_service: Parses a service from the rail data.
    parse_departures: Parses the departures from the provided train services data for a
    specific platform.
    parse_nrcc_message: Parses the NRCC messages from the provided data.
    parse_rail_data: Parses the rail data to get the first two departures for the station
    and platform specified in config.py
    """

    def __init__(self):
        self.nrcc_message = ""
        self.oled1_departures = []
        self.oled2_departures = []
        self.get_rail_data_count = 0
        self.api_fails = 0
        self.api_retry_secs = config.BASE_API_UPDATE_INTERVAL

    async def fetch_data_from_api(self):
        """
        Asynchronously fetches rail data from the API.

        This method checks if the wifi is connected, constructs the API URL and headers based
        on the configuration, makes a GET request to the API, checks the response status code,
        logs the size of the response data, loads the JSON data from the response, and returns
        the JSON data.

        Raises:
        AssertionError: If the wifi is not connected.
        OSError: If there is no response from the API or if the response status code is not in the
        range 200-299.

        Returns:
        dict: A dictionary representing the JSON data from the API response.
        """
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

                # Timeout raises requests.exceptions.Timeout, a subclass of IOError
                response = requests.get(
                    url=config.AWS_API_URL, headers=rail_data_headers, timeout=10
                )

            if not response:
                log_message("No response from API", level="ERROR")
                raise OSError("No response from API")

            if response.status_code < 200 or response.status_code >= 300:
                log_message(
                    f"HTTP request failed. Status code {response.status_code}. "
                    "Contents: {response.text[:200]}",
                    level="ERROR",
                )
                raise OSError(
                    f"HTTP request failed. Status code {response.status_code}. "
                    "Contents: {response.text[:200]}"
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
        """
        Returns a summary of the departures.

        This method takes a list of departures and returns a string that either says "No departures"
        if the list is empty, or contains the destination and scheduled time of the first
        two departures.

        Parameters:
        departures (list): A list of dictionaries, each representing a departure. Each dictionary
        should have keys "destination" and "time_scheduled".

        Returns:
        str: A string that either says "No departures" or contains the destination and scheduled
        time of the first two departures.
        """

        def get_departure(d):
            return f"{d['destination']} ({d['time_scheduled']})"

        return (
            "No departures"
            if not departures
            else " and ".join(get_departure(d) for d in departures[:2])
        )

    def get_offline_rail_data(self):
        """
        Fetches rail data from a file and updates the OLED displays.

        This method increments the count of data fetches, logs the call number and free memory,
        opens the offline data file, loads the JSON data from the file, parses the rail data,
        collects garbage, gets the departure summary for both displays, and logs the
        departure summaries.

        Raises:
        OSError: If there is an error opening or reading the file.
        ValueError: If there is an error loading the JSON data from the file.
        """
        self.get_rail_data_count += 1
        log_message(
            f"get_offline_rail_data call {self.get_rail_data_count}. " +
            f"Free memory: {gc.mem_free()}",  # pylint: disable=no-member
            level="DEBUG",
        )

        try:
            with open(
                config.OFFLINE_JSON_FILE, "r", encoding="utf-8"
            ) as offline_data_file:
                response_json = ujson.load(offline_data_file)
        except OSError as e:
            log_message(f"Error opening or reading file: {e}", level="ERROR")
            raise
        except ValueError as e:
            log_message(f"Error loading file JSON: {e}", level="ERROR")
            raise

        self.parse_rail_data(response_json)
        gc.collect()

        oled1_summary = self.get_departure_summary(self.oled1_departures)
        oled2_summary = self.get_departure_summary(self.oled2_departures)

        log_message(
            "[OFFLINE] get_offline_rail_data() got oled1_departures " +
            f"(Platform {config.OLED1_PLATFORM_NUMBER}): {oled1_summary} " +
            "and oled2_departures" +
            f"(Platform {config.OLED2_PLATFORM_NUMBER}): {oled2_summary}",
            level="INFO",
        )

    async def get_online_rail_data(self, oled1, oled2):
        """
        Asynchronously fetches rail data from the API and updates the OLED displays.

        This method increments the count of API calls, logs the call number and free memory,
        saves the current screen contents, displays a message on both screens, fetches the
        rail data from the API, parses the rail data, collects garbage, restores the displays,
        gets the departure summary for both displays, and logs the departure summaries.

        Parameters:
        oled1 (SSD1306_I2C): The first OLED display object.
        oled2 (SSD1306_I2C): The second OLED display object.

        Raises:
        OSError: If there is a system-level error.
        """
        self.get_rail_data_count += 1
        log_message(
            f"get_online_rail_data call {self.get_rail_data_count}. " +
            f"Free memory: {gc.mem_free()}",  # pylint: disable=no-member
            level="DEBUG",
        )

        # Save the current screen contents
        oled1_before = oled1.save_buffer()
        oled2_before = oled2.save_buffer()

        display_utils.both_screen_text(oled1, oled2, "Updating trains", 12)

        response_json = await self.fetch_data_from_api()

        self.parse_rail_data(response_json)
        gc.collect()

        # Restore the displays
        oled1.restore_buffer(oled1_before)
        oled2.restore_buffer(oled2_before)
        oled1.show()
        oled2.show()

        oled1_summary = self.get_departure_summary(self.oled1_departures)
        oled2_summary = self.get_departure_summary(self.oled2_departures)

        log_message(
            "[ONLINE] get_online_rail_data() got oled1_departures "
            f"(Platform {config.OLED1_PLATFORM_NUMBER}): {oled1_summary} " +
            f"and oled2_departures (Platform {config.OLED2_PLATFORM_NUMBER}): {oled2_summary}",
            level="DEBUG",
        )

    async def cycle_get_online_rail_data(self, oled1, oled2):
        """
        Continuously updates rail data from the API at a specified interval.

        This method runs an infinite loop that fetches online rail data and updates the OLED
        displays.
        If the API call fails, it backs off exponentially, up to a maximum delay of 180 seconds.
        The delay between API calls is reset to the base interval upon a successful API call.

        Parameters:
        oled1 (SSD1306_I2C): The first OLED display object.
        oled2 (SSD1306_I2C): The second OLED display object.

        Raises:
        OSError: If there is a system-level error.
        ValueError: If a function receives an argument of the correct type but inappropriate value.
        TypeError: If a function receives an argument of an inappropriate type.
        MemoryError: If a memory allocation fails.
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
                    f"API request success. Next call in {self.api_retry_secs} seconds.",
                    level="INFO",
                )
            except (IOError, OSError, ValueError, TypeError, MemoryError) as e:
                self.api_fails += 1
                self.api_retry_secs = min(5 * 2 ** (self.api_fails - 1), 180)
                log_message(
                    f"API request fail #{self.api_fails}: {e}. " +
                    f"Next retry in {self.api_retry_secs} seconds.",
                    level="ERROR",
                )

    def parse_service(self, service):
        """
        Parses a service from the rail data.

        This method takes a service dictionary and extracts the destination, scheduled time,
        estimated time, operator, and subsequent calling points. If the estimated time is "On time",
        the scheduled time is used instead.

        Parameters:
        service (dict): A dictionary representing a service from the rail data.

        Returns:
        dict: A dictionary with keys "destination", "time_scheduled", "time_estimated",
        "operator", and "subsequentCallingPoints". The "subsequentCallingPoints" value is a list
        of tuples, each containing a location name and either the estimated time or the scheduled
        time if the estimated time is "On time".

        Raises:
        ValueError: If the service parameter is not provided.
        """
        if not service:
            raise ValueError("service is required")

        subsequent_calling_points = [
            (
                calling_point.get("locationName"),
                (
                    calling_point.get("et")
                    if calling_point.get("et") != "On time"
                    else calling_point.get("st")
                ),
            )
            for subsequent_calling_point in service.get("subsequentCallingPoints", [])
            for calling_point in subsequent_calling_point.get("callingPoint", [])
        ]

        return {
            "destination": service.get("destination", [{}])[0].get("locationName"),
            "time_scheduled": service.get("std"),
            "time_estimated": service.get("etd"),
            "operator": service.get("operator"),
            "subsequentCallingPoints": subsequent_calling_points,
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
            list: A list of dictionaries, each representing a parsed train service departing
            from the specified platform.
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

    def parse_rail_data(self, data_json):
        """
        Parse the rail data to get the first two departures for the station and platform specified
        in config.py
        Within the next 120 minutes (default/max)
        Plus any NRCC Travel Alert message.
        """
        try:
            if data_json:
                train_services = data_json.get("trainServices", [])

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
                    if data_json.get("nrccMessages"):
                        self.nrcc_message = self.parse_nrcc_message(
                            data_json.get("nrccMessages")
                        )
        except (ValueError, TypeError, MemoryError, OSError) as error:
            log_message(f"Error parsing rail data JSON: {error}", level="ERROR")


async def main():
    """
    The main entry point of the program.

    This method connects to the wifi, sets the time, creates an instance of RailData,
    and starts the cycle of getting online rail data. It also logs the loop count and
    free memory, and collects garbage every 5 loops. If the wifi is not connected, it
    logs an error message and exits.

    Raises:
    OSError: If there is a system-level error.
    ValueError: If a function receives an argument of the correct type but inappropriate value.
    TypeError: If a function receives an argument of an inappropriate type.
    MemoryError: If a memory allocation fails.
    """
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
