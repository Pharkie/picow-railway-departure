import urequests
import ujson

# Replace with your WLED device's IP address
WLED_IP = "192.168.8.137"

def send_command_to_wled(command):
    url = f"http://{WLED_IP}/json/state"
    headers = {"Content-Type": "application/json"}
    data = ujson.dumps(command)
    response = urequests.post(url, headers=headers, data=data)
    return response.json()

# # Turn on the WLED device
# command = {"on": True}

# Set the effect to preset 1
command = {"ps": 1}

response = send_command_to_wled(command)
print(response)