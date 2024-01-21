# This is a lambda function that runs on AWS Lambda. It's called by the API Gateway.
# It fetches data from the National Rail API and filters it to only include services from the requested platform(s).

import json
import requests
import time


def keep_keys_in_dict(dict_del, keys):
    keys_set = set(keys)
    keys_with_subkeys = {k.split(".")[0] for k in keys if "." in k}

    for key in list(dict_del.keys()):
        if key not in keys_set and key not in keys_with_subkeys:
            del dict_del[key]
        elif isinstance(dict_del[key], dict):
            subkeys = [k.split(".", 1)[1] for k in keys if k.startswith(key + ".")]
            keep_keys_in_dict(dict_del[key], subkeys)
        elif isinstance(dict_del[key], list):
            for item in dict_del[key]:
                if isinstance(item, dict):
                    subkeys = [
                        k.split(".", 1)[1] for k in keys if k.startswith(key + ".")
                    ]
                    keep_keys_in_dict(item, subkeys)
                elif isinstance(item, list):
                    for subitem in item:
                        if isinstance(subitem, dict):
                            subkeys = [
                                k.split(".", 1)[1]
                                for k in keys
                                if k.startswith(key + ".")
                            ]
                            keep_keys_in_dict(subitem, subkeys)


def lambda_handler(event, context):
    # Get CRS code from path parameters
    crs_code = event.get("pathParameters", {}).get("CRS")
    if not crs_code:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "CRS path parameter is required"}),
        }

    headers = event.get("headers")
    if headers is None:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "No headers found in the request"}),
        }

    # Get API key from headers
    api_key = headers.get("x-apikey")
    if api_key is None:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "x-apikey header is required"}),
        }

    # Get optional platform numbers from query parameters and split into a list
    queryStringParameters = event.get("queryStringParameters")
    platform_numbers = None
    if queryStringParameters is not None:
        platforms_param = queryStringParameters.get("platforms")
        if platforms_param is not None:
            platform_numbers = platforms_param.split(",")

    # Define API URL and headers
    LDBWS_API_URL = (
        f"https://api1.raildata.org.uk"
        f"/1010-live-departure-board-dep/LDBWS/api/20220120/GetDepBoardWithDetails/{crs_code}"
    )

    request_headers = {"x-apikey": api_key}

    # Fetch rail data
    MAX_RETRIES = 3
    DELAY_BETWEEN_RETRIES = 0.2  # Delay in seconds

    for i in range(MAX_RETRIES):
        try:
            print(
                f"[AWS] Starting attempt {i+1} of {MAX_RETRIES} to fetch rail data from RailData API."
            )
            response = requests.get(LDBWS_API_URL, headers=request_headers)
            response.raise_for_status()  # Raise an exception if the response contains an HTTP error status code
            data = response.json()
            print(f"[AWS] Success: got RailData JSON back on attempt {i+1}.")
            break  # If the request was successful, break out of the loop
        except requests.exceptions.RequestException as e:
            print(
                f"[AWS] [Error] On attempt {i+1} of {MAX_RETRIES} got error: {str(e)}."
            )
            if (
                i == MAX_RETRIES - 1
            ):  # If this was the last attempt, re-raise the exception
                return {
                    "statusCode": 500,
                    "body": json.dumps(
                        {"error": "Failed to fetch rail data: " + str(e)}
                    ),
                }
            else:  # Otherwise, log the error, wait for a while and continue to the next iteration
                print(f"[AWS] Retrying RailData API in {DELAY_BETWEEN_RETRIES} seconds")
                time.sleep(DELAY_BETWEEN_RETRIES)

    # Filter services based on platform and only include specific fields
    # Specify the fields to keep. Rest are deleted. Parents of subkeys specified are kept.
    keys_to_keep = [
        "platform",
        "std",
        "etd",
        "operator",
        "subsequentCallingPoints.callingPoint.locationName",
        "subsequentCallingPoints.callingPoint.st",
        "subsequentCallingPoints.callingPoint.et",
        "destination.locationName",
    ]

    print(
        "[AWS] Filtering services based on platform and only including specific fields."
    )
    filtered_services = []
    for service in data.get("trainServices", []):
        if platform_numbers is None or (
            service.get("platform") and service.get("platform") in platform_numbers
        ):
            keep_keys_in_dict(service, keys_to_keep)
            filtered_services.append(service)
    print(f"[AWS] Success: filtered services.")

    # Limit to the first two services for each platform
    platform_services = {}
    for service in filtered_services:
        platform = service.get("platform")
        if platform not in platform_services:
            platform_services[platform] = []
        if len(platform_services[platform]) < 2:
            platform_services[platform].append(service)

    # Flatten the dictionary to a list
    print("[AWS] Flattening the dictionary to a list.")
    filtered_services = [
        service for services in platform_services.values() for service in services
    ]

    print(f"[AWS] Final list of services to send as response: {filtered_services}")

    # Return the filtered data inside the trinaServices key
    return {"statusCode": 200, "body": json.dumps({"trainServices": filtered_services})}
