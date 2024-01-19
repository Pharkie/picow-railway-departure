import uhashlib as hashlib
import hmac
import utime
import ubinascii as _ubinascii
import credentials
import urequests
import config

def request_gen(
    access_key,
    secret_key,
    date_time_stamp,
    method="POST",
    region=config.AWS_REGION,
    body="",
    uri="",
):
    service = "logs"
    request_type = "aws4_request"
    algorithm = "AWS4-HMAC-SHA256"

    date_stamp = date_time_stamp[:8]

    return_dict = {}
    return_dict["host"] = f"{service}.{region}.amazonaws.com"
    return_dict["uri"] = "/"

    key = bytearray()
    key.extend(("AWS4" + secret_key).encode())
    print("Key: ", key)
    kDate = hmac.new(key, date_stamp.encode('utf-8'), 'sha256').digest()
    kRegion = hmac.new(kDate, region.encode('utf-8'), 'sha256').digest()
    kService = hmac.new(kRegion, service.encode('utf-8'), 'sha256').digest()
    kSigning = hmac.new(kService, request_type.encode('utf-8'), 'sha256').digest()

    content_length = str(len(body))
    print(f"Body: {body}\n")
    payload_hash = _ubinascii.hexlify(hashlib.sha256(body.encode("utf-8")).digest()).decode(
        "utf-8"
    )

    # make the string to sign
    canonical_querystring = ""  # no request params for logs

    canonical_headers_dict = {
        "content-type": "application/x-amz-json-1.1",
        "host": return_dict["host"],
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": date_time_stamp,
        "x-amz-target": "Logs_20140328.PutLogEvents",
    }
    # Build the canonical headers string
    canonical_headers = "\n".join(
        f"{key}:{value}" for key, value in canonical_headers_dict.items()
    )
    # Get the sorted keys for signed_headers
    signed_headers = ";".join(
        sorted(key.lower() for key in canonical_headers_dict.keys())
    )

    canonical_request = (
        method
        + "\n"
        + return_dict["uri"]
        + "\n"
        + canonical_querystring
        + "\n"
        + canonical_headers
        + "\n"
        + signed_headers
        + "\n"
        + payload_hash
    )


    canonical_request_hash = _ubinascii.hexlify(
        hashlib.sha256(canonical_request.encode("utf-8")).digest()
    ).decode("utf-8")


    credential_scope = date_stamp + "/" + region + "/" + service + "/" + request_type
    string_to_sign = (
        algorithm
        + "\n"
        + date_time_stamp
        + "\n"
        + credential_scope
        + "\n"
        + canonical_request_hash
    )

    # generate the signature:
    signature = hmac.new(kSigning, string_to_sign.encode('utf-8'), 'sha256').digest()
    signature_hex = _ubinascii.hexlify(signature).decode("utf-8")

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
        + signature_hex
    )

    return_dict["headers"] = {
        "authorization": authorization_header,
        "content-type": "application/x-amz-json-1.1",
        "host": return_dict["host"],
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": date_time_stamp,
        "x-amz-target": "Logs_20140328.PutLogEvents",
    }

    return return_dict

def main():
    # Replace these with your actual access key and secret key
    access_key = credentials.AWS_ACCESS_KEY
    secret_key = credentials.AWS_SECRET_ACCESS_KEY
    # url = config.AWS_API_URL

    # Get the current date and time in the format required by AWS
    now = utime.localtime()
    date_time_stamp = f"{now[0]:04d}{now[1]:02d}{now[2]:02d}T{now[3]:02d}{now[4]:02d}{now[5]:02d}Z"

    # Call the request_gen function
    request_info = request_gen(access_key, secret_key, date_time_stamp)

    # print('Host:', request_info['host'])
    # print('URI:', request_info['uri'])  

    # Combine the host and URI to form the URL
    api_url = 'https://' + request_info['host'] + request_info['uri']

    print(f"Calling URL: {api_url}\n")
    print(f"Headers: {request_info['headers']}\n")

    # Send the request
    response = urequests.get(api_url, headers=request_info['headers'])

    # Print the response
    print(f"Response status code: {response.status_code}")
    print(f"Response: {response.text}\n")

# Call the main function
if __name__ == "__main__":
    main()