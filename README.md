# Mini Pico W OLED Departure Boards for Model Railway

This project uses a Raspberry Pi Pico with an OLED display to show departure boards for a model railway.

## Author

Adam Knowles

## Version

0.1

## Description

This project uses a Raspberry Pi Pico with an OLED display to show departure boards for a model railway. The departure data is fetched from a remote server and displayed on the OLED display.

## Features

1. **Live, real-time Departure Data**: Fetches real-time departure data from raildata.org.uk via a product from the Rail Data Group. This data source is reliable, free, for personal/hobby use, with unlimited access. The program also syncs the current time on startup.

2. **Made for Raspberry Pi Pico**: Built for the Raspberry Pi Pico, a cheap, easily available, small and versatile microcontroller.

3. **Runs two platform screens**: Runs one or two OLED (SSD1306) screens, the maximum for the 2 x I2C buses on the Pico. Each screen displays the first and second departures for that platform. Each screen will also show the "due" time for any delays on the first departure, the calling points for the first departure, and any travel alerts.

4. **Consumes Rail Data API or AWS filtered API**: you can choose to call the Rail Data API direct for requests where the response size will be small enough to fit in the Pico's memory. For bigger API responses (e.g. CRS=EUS), you may filter the Rail Data API using an AWS API gateway and Lamdba function. FOr AWS, you'll need to set up services in your AWS account based on the code provided.

5. **Resilience**: Designed for run-all-day operation. Will re-attempt API calls before stopping.

6. **Offline mode**: Can be set to a simple offline mode that uses the info stored in sample_data.json - taken from an API response that you wish to re-use.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/Pharkie/picow-railway-departure.git
    ```

2. Navigate to the project directory

## Usage

1. Run main.py

## Known Issues

The application doesn't handle DST change while the device is running, since it only checks at startup.

Large responses from Rail Data API likely to crash the system (use AWS API instead).

## License

This project is licensed under the GNU General Public License (GPL).

## Acknowledgements

This project is based on work by Stewart Watkiss - PenguinTutor. 

Models for the 3D printed casing for the OLED panel(s) can be found in the upstream repo, as can docs for the SSD1306 and some other aspects I didn't wish to duplicate or extend.