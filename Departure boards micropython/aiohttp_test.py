import aiohttp
import asyncio

request_headers = {"x-apikey": "dW6IyEZxSwkO5IDe1JwgYzs02GTGGEAnxnteqebIqN6GSA19"}

LDBWS_API_URL = ( # National Rail API URL. On two lines for readability.
    "https://api1.raildata.org.uk"
    "/1010-live-departure-board-dep/LDBWS/api/20220120/GetDepBoardWithDetails/PMW"
)

async def main():
    async with aiohttp.ClientSession(headers=request_headers) as session:
        async with session.get(LDBWS_API_URL) as r:
            json_body = await r.json()
            print(json_body)

asyncio.run(main())