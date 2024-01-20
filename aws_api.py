import hmac
import uhashlib as hashlib
import ubinascii
import utime
import urequests
import json
import config
import credentials

def getSignatureKey(secret_key, date_stamp, regionName, serviceName):
    kDate = sign(('AWS4' + secret_key).encode('utf-8'), date_stamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning

def create_signed_headers(
    api_host,
    api_uri,
    region,
    service,
    access_key,
    secret_key,
    http_method='GET',
    query_string='',
    additional_headers=None,
    payload=''
):
    # Create a date for headers and the credential string
    t = utime.gmtime()
    amz_date = f"{t[0]:04d}{t[1]:02d}{t[2]:02d}T{t[3]:02d}{t[4]:02d}{t[5]:02d}Z"
    date_stamp = f"{t[0]:04d}{t[1]:02d}{t[2]:02d}"

    # Prepare canonical request
    canonical_querystring = query_string
    canonical_headers = 'host:' + api_host + '\n' + 'x-amz-date:' + amz_date + '\n'
    signed_headers = 'host;x-amz-date'
    payload = '' # GET requests don't usually have a payload
    payload_hash = ubinascii.hexlify(hashlib.sha256(payload.encode('utf-8')).digest()).decode()

    # print(f"\npayload_hash: {payload_hash}\n")
    
    canonical_request = (
        http_method + '\n' + api_uri + '\n' + canonical_querystring + '\n' +
        canonical_headers + '\n' + signed_headers + '\n' + payload_hash
    )

    # Prepare string to sign
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = date_stamp + '/' + region + '/' + service + '/' + 'aws4_request'
    string_to_sign = (
        algorithm + '\n' +  amz_date + '\n' +  credential_scope + '\n' +
        ubinascii.hexlify(hashlib.sha256(canonical_request.encode('utf-8')).digest()).decode()
    )

    # Calculate the signature
    signing_key = getSignatureKey(secret_key, date_stamp, region, service)
    signature = hmac.new(
        signing_key, string_to_sign.encode('utf-8'), digestmod='sha256'
    ).hexdigest()

    # Prepare authorization header
    authorization_header = (
        algorithm + ' ' + 'Credential=' + access_key + '/' + credential_scope + ', ' +
        'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature
    )

    # Prepare headers
    headers = {'x-amz-date':amz_date, 'Authorization':authorization_header}
    
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
    return hmac.new(key, msg.encode("utf-8"), digestmod='sha256').digest()

def main():
    additional_headers = {'x-apikey': credentials.RAILDATAORG_API_KEY}
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
        payload=payload
    )

    try:
        if http_method == 'GET':
            response = urequests.get(config.AWS_API_URL, headers=headers)
        elif http_method == 'POST':
            response = urequests.post(config.AWS_API_URL, headers=headers, data=payload)
        elif http_method == 'PUT':
            response = urequests.put(config.AWS_API_URL, headers=headers, data=payload)
        elif http_method == 'DELETE':
            response = urequests.delete(config.AWS_API_URL, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {http_method}")
        
        if response.status_code < 200 or response.status_code >= 400:
            print(f"Request failed with status code {response.status_code}")
            return
    except Exception as e:
        print(f"Request failed: {e}")
        return

    print(response.text)

    response_json = json.loads(response.text)

    print(json.dumps(response_json))

    # Use this troubleshooting AWS. Get the message and any error from the response
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

if __name__ == "__main__":
    main()