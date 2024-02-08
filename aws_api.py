"""
Author: Adam Knowles
Version: 0.1
Name: aws_api.py
Description: Interface with AWS API. Signs a request with AWS credentials and an API key.

GitHub Repository: https://github.com/Pharkie/picow-railway-departure
License: GNU General Public License (GPL)
"""

import hmac
import hashlib

# import json
import ubinascii  # pylint: disable=import-error
import utime
import requests
import config
import credentials


def get_signature_key(secret_key, date_stamp, region_name, service_name):
    """
    Generates a signing key for AWS API requests.

    Parameters:
    secret_key (str): The AWS secret key.
    date_stamp (str): The date in YYYYMMDD format.
    regionName (str): The AWS region name.
    serviceName (str): The AWS service name.

    Returns:
    bytes: The signing key.
    """
    k_date = sign(("AWS4" + secret_key).encode("utf-8"), date_stamp)
    k_region = sign(k_date, region_name)
    k_service = sign(k_region, service_name)
    k_signing = sign(k_service, "aws4_request")
    return k_signing


def create_signed_headers(
    api_host,
    api_uri,
    region,
    service,
    access_key,
    secret_key,
    http_method="GET",
    query_string="",
    additional_headers=None,
    payload="",
):
    """
    Creates signed headers for AWS API requests.

    Parameters:
    api_host (str): The API host.
    api_uri (str): The API URI.
    region (str): The AWS region.
    service (str): The AWS service.
    access_key (str): The AWS access key.
    secret_key (str): The AWS secret key.
    http_method (str, optional): The HTTP method. Defaults to "GET".
    query_string (str, optional): The query string. Defaults to "".
    additional_headers (dict, optional): Additional headers. Defaults to None.
    payload (str, optional): The payload. Defaults to "".

    Returns:
    dict: The signed headers.
    """
    # Create a date for headers and the credential string
    t = utime.gmtime()
    amz_date = f"{t[0]:04d}{t[1]:02d}{t[2]:02d}T{t[3]:02d}{t[4]:02d}{t[5]:02d}Z"
    date_stamp = f"{t[0]:04d}{t[1]:02d}{t[2]:02d}"

    # Prepare canonical request
    canonical_querystring = query_string
    canonical_headers = (
        "host:" + api_host + "\n" + "x-amz-date:" + amz_date + "\n"
    )
    signed_headers = "host;x-amz-date"
    payload = ""  # GET requests don't usually have a payload
    payload_hash = ubinascii.hexlify(
        hashlib.sha256(payload.encode("utf-8")).digest()
    ).decode()

    # print(f"\npayload_hash: {payload_hash}\n")

    canonical_request = (
        http_method
        + "\n"
        + api_uri
        + "\n"
        + canonical_querystring
        + "\n"
        + canonical_headers
        + "\n"
        + signed_headers
        + "\n"
        + payload_hash
    )

    # Prepare string to sign
    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = (
        date_stamp + "/" + region + "/" + service + "/" + "aws4_request"
    )
    string_to_sign = (
        algorithm
        + "\n"
        + amz_date
        + "\n"
        + credential_scope
        + "\n"
        + ubinascii.hexlify(
            hashlib.sha256(canonical_request.encode("utf-8")).digest()
        ).decode()
    )

    # Calculate the signature
    signing_key = get_signature_key(secret_key, date_stamp, region, service)
    signature = hmac.new(
        signing_key, string_to_sign.encode("utf-8"), digestmod="sha256"
    ).hexdigest()

    # Prepare authorization header
    authorization_header = (
        algorithm
        + " "
        + "Credential="
        + access_key
        + "/"
        + credential_scope
        + ", "
        + "SignedHeaders="
        + signed_headers
        + ", "
        + "Signature="
        + signature
    )

    # Prepare headers
    headers = {"x-amz-date": amz_date, "Authorization": authorization_header}

    if additional_headers is not None:
        headers.update(additional_headers)

    # print("================================")
    # print("Canonical Request")
    # print("================================")
    # print(http_method) # HTTPRequestMethod
    # print(api_uri) # CanonicalURI
    # print(canonical_querystring) # CanonicalQueryString
    # print(canonical_headers) # CanonicalHeaders
    # print(signed_headers) # SignedHeaders
    # print(payload_hash) # HashedPayload
    # print("================================")
    # print("String-to-sign")
    # print("================================")
    # print(string_to_sign)

    return headers


def sign(key, msg):
    """
    Generates a HMAC-SHA256 signature for a message.

    Parameters:
    key (bytes): The secret key for the HMAC operation.
    msg (str): The message to sign.

    Returns:
    bytes: The HMAC-SHA256 signature of the message.
    """
    return hmac.new(key, msg.encode("utf-8"), digestmod="sha256").digest()


def main():
    """
    Test this module.
    Sends a request to the AWS API and prints the response.

    The request is signed with AWS credentials and an API key. The HTTP method and payload can be
    customized. If the request fails, an error message is printed and the function returns early.

    Side Effects:
    Sends a request to the AWS API and prints the response or an error message.
    """
    additional_headers = {"x-apikey": credentials.RAILDATAORG_API_KEY}
    payload = ""
    http_method = "GET"

    headers = create_signed_headers(
        api_host=config.AWS_API_HOST,
        api_uri=config.AWS_API_URI,
        region=config.AWS_API_REGION,
        service=config.AWS_API_SERVICE,
        access_key=credentials.AWS_ACCESS_KEY,
        secret_key=credentials.AWS_SECRET_ACCESS_KEY,
        query_string=config.AWS_API_QUERYSTRING,
        additional_headers=additional_headers,
        http_method=http_method,
        payload=payload,
    )

    try:
        if http_method == "GET":
            response = requests.get(config.AWS_API_URL, headers=headers)
        elif http_method == "POST":
            response = requests.post(
                config.AWS_API_URL, headers=headers, data=payload
            )
        elif http_method == "PUT":
            response = requests.put(
                config.AWS_API_URL, headers=headers, data=payload
            )
        elif http_method == "DELETE":
            response = requests.delete(config.AWS_API_URL, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {http_method}")

        if response.status_code < 200 or response.status_code >= 400:
            print(f"Request failed with status code {response.status_code}")
            return
    except (OSError, ValueError, TypeError, MemoryError) as e:
        print(f"Request failed: {e}")
        return

    # response_json = json.loads(response.text)

    # # Use this troubleshooting AWS. Get the message and any error from the response
    # message = response_json.get('message')
    # error = response_json.get('error')

    # print("================================")
    # print("Response")
    # print("================================")
    # if message is not None:
    #     message = message.replace("'", "") # Remove single quotes to make comparison easier
    #     print(f"Message: {message}")
    # if error is not None:
    #     print(f"Error: {error}")

    print(response.text)
    # print(json.dumps(response_json))


if __name__ == "__main__":
    main()
