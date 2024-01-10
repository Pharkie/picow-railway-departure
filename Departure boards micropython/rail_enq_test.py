"""
Access the National Rail API to get departure information.
"""
import urequests
import re

API_KEY = "dW6IyEZxSwkO5IDe1JwgYzs02GTGGEAnxnteqebIqN6GSA19"  # Replace with your API key
STATION_CRS = "PMW"  # Replace with your station's CRS code

def get_ldbws_api_data():
    """
    Function to get data from the National Rail API.
    """
    try:
        base_url = "https://api1.raildata.org.uk/1010-live-departure-board-dep/LDBWS/api/20220120/GetDepBoardWithDetails"
        url = f"{base_url}/{STATION_CRS}"
        headers = {"x-apikey": API_KEY}
        response = urequests.get(url, headers=headers)
        data = response.json()
        return data
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_departures(api_data):
    """
    Get the first two departures from the National Rail API.
    """
    if api_data:
        # Get the first two departures
        departures = [{
            "destination": api_data["trainServices"][i]["destination"][0]["locationName"],
            "time_due": api_data["trainServices"][i]["std"],
            "platform": api_data["trainServices"][i]["platform"]
        } for i in range(2)]
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

ldbws_api_data = get_ldbws_api_data()

nrcc_message = get_nrcc_msg(ldbws_api_data)
if nrcc_message:
    print("Alert:", nrcc_message, "\n")

departures_list = get_departures(ldbws_api_data)
if departures_list:
    for departure in departures_list:
        print("Train to:", departure["destination"])
        print("Departure time:", departure["time_due"])
        print("Platform:", departure["platform"])
        print()  # Add a newline between departures
else:
    print("No departures found.")