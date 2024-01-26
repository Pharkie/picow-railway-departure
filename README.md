# Mini Pico W OLED Departure Boards for Model Railway

This project uses a Raspberry Pi Pico with an OLED display to show departure boards for a model railway.

## Author

Adam Knowles

## Version

0.1

## Description

This project uses a Raspberry Pi Pico with an OLED display to show departure boards for a model railway. The departure data is fetched from a remote server and displayed on the OLED display.

## Features

1. **Live, real-time Departure Data**: Fetches real-time departure data from raildata.org.uk via a product from the Rail Data Group. This data source is reliable, free, for personal/hobby use, with unlimited access.

2. **Made for Raspberry Pi Pico**: Built for the Raspberry Pi Pico, a cheap, easily available, small and versatile microcontroller.

3. **Runs two platform screens**: Runs one or two OLED (SSD1306) screens, the maximum for the 2 x I2C buses on the Pico. Each screen displays the first and second departures for that platform. Each screen will also show the "due" time for any delays on the first departure, the calling points for the first departure, and any travel alerts. You can also set your own message as a "travel alert, instead.

4. **Consumes Rail Data API or AWS filtered API**: you can choose to call the Rail Data API direct for requests where the response size will be small enough to fit in the Pico's memory. For bigger API responses (e.g. CRS=EUS), you may filter the Rail Data API using an AWS API intermediary.

5. **Resilience**: Designed for run-all-day operation. Will re-attempt failed API calls with back-off timings. Logs files are recorded on the device with a configurable level of logging. Time is synced via NTP on startup, then daylight saving time (DST) change (UK/BST) is checked for change once per minute.

6. **Offline mode**: Can be set to a simple offline mode that uses the info stored in sample_data.json - taken from an API response that you wish to re-use.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/Pharkie/picow-railway-departure.git
    ```

2. Navigate to the project directory

## AWS API intermediary

Using an AWS intermediary between the Pico and the Rail Data API makes two contributions:

1. Unused keys in the JSON response are deleted, making for a smaller API response (1-5 kb rather than 30-80kb). This stops the Pico running out of memory trying to parse large API responses.
2. The AWS code will retry the Rail Data API, if necessary, up to 3 times in 8 seconds. This covers over any occasional, temporary errors calling the Rail Data API and makes a more reliable experience for the Pico.

## AWS Setup

To use an AWS API intermediary, you'll need to set up services in your AWS account, based on the code provided.

1. Paste the contents of "aws_lambda_function.py" into a Lambda function running Python.
2. Set up an API Gateway endpoint to call the lambda function. Put the API endpoint URL into "config.py".
3. Configure IAM credentials so the API Gateway and Lambda function are callable. Put the access_key and secret_access_key in "credential.py".
4. Configure Cloudwatch Alarms on the logs or other metrics to email you about Errors (optional)

If you want a video tutorial, let me know.

## Usage

1. Run main.py

## Known Issues

* Clock may skip a second, every now and then, due to the device being busy elsewhere.
* Large responses from Rail Data API likely to crash the system. Use the AWS API intermediary instead.

## License

This project is licensed under the GNU General Public License (GPL).

## Acknowledgements

This project is based on work by Stewart Watkiss - PenguinTutor. 

Models for the 3D printed casing for the OLED panel(s) can be found in the upstream repo, as can docs for the SSD1306 and some other aspects I didn't wish to duplicate or extend.