import urllib.urequest

def test_get_request():
    response = urllib.urequest.urlopen('http://httpbin.org/get')
    response_content = response.read()
    print(f"Response content: {response_content}")

if __name__ == '__main__':
    test_get_request()