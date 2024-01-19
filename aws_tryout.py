import hmac
import urequests
import uhashlib as hashlib
import ubinascii
import utime
import config
import credentials

def create_signed_headers(url, region, service, access_key, secret_key):
    # Create a date for headers and the credential string
    t = utime.gmtime()
    amz_date = "{:04d}{:02d}{:02d}T{:02d}{:02d}{:02d}Z".format(*t)
    date_stamp = "{:04d}{:02d}{:02d}".format(*t)

    # Prepare canonical request
    method = 'GET'
    canonical_uri = '/' 
    canonical_querystring = '' 
    canonical_headers = 'host:' + url + '\n' + 'x-amz-date:' + amz_date + '\n'
    signed_headers = 'host;x-amz-date'
    payload_hash = ubinascii.hexlify(hashlib.sha256('').digest()).decode()
    canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash

    # Prepare string to sign
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = date_stamp + '/' + region + '/' + service + '/' + 'aws4_request'
    string_to_sign = algorithm + '\n' +  amz_date + '\n' +  credential_scope + '\n' + ubinascii.hexlify(hashlib.sha256(canonical_request.encode('utf-8')).digest()).decode()

    # Calculate the signature
    signing_key = getSignatureKey(secret_key, date_stamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), 'SHA256').hexdigest()

    # Prepare authorization header
    authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature

    # Prepare headers
    headers = {'x-amz-date':amz_date, 'Authorization':authorization_header}

    return headers

def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), digestmod='SHA256').hexdigest()

def getSignatureKey(key, date_stamp, regionName, serviceName):
    kDate = sign(('AWS4' + key).encode('utf-8'), date_stamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning

def main():
    url = config.AWS_API_URL
    region = config.AWS_REGION
    service = 'execute-api'
    headers = create_signed_headers(url, region, service, credentials.AWS_ACCESS_KEY, credentials.AWS_SECRET_ACCESS_KEY)
    response = urequests.get(url, headers=headers)
    print(response.text)

if __name__ == "__main__":
    main()